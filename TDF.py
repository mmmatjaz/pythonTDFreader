import struct
import numpy as np


    
class TDF(object):
    """ TDF protocol constants """
    tdfSignature = '41604B82CA8411D3ACB60060080C6816'
    tdfData3DBlockId = 5
    tdfDataGPBlockId = 14

    """ instance members
    marker data 
        freqM
        labelsM
        markers
        timeM
    
    analogue input data 
        freqA
        labelsA
        analogue
        timeA
    """
    
    def __init__(self, fileName):
        try:
            block3d, blockIn = TDF.validateFile(fileName)
            self.markers, self.labelsM, self.freqM, nFrames, startTime = \
                TDF.get3Ddata(fileName, block3d)
            self.timeM=startTime+np.arange(0,nFrames)/self.freqM
            self.analogue, self.labelsA, self.freqA,nFrames, startTime, gpMap = \
                TDF.getAnalogue(fileName, blockIn)
            self.timeA = startTime + np.arange(0, nFrames) / self.freqA
        except Warning as e:
            # data missing
            print(e.args)
        except IOError as e:
            print(e.args)

    
    def getMarkerTime(self):
        return 

    @staticmethod
    def validateFile(fileName):
        with open(fileName, 'rb') as fid:
            fileSign = "".join(["{:08x}".format(b4) for b4 in struct.unpack('IIII', fid.read(4 * 4))])
            if (fileSign!=TDF.tdfSignature.lower()):
                #print("invalid file")
                raise IOError("invalid file")

            version,nEntries  = struct.unpack('Ii', fid.read(4*2))

            if nEntries <= 0:
                #print('The file specified contains no data.')
                raise IOError('The file specified contains no data.')

            nextEntryOffset = 40
            #tdfBlockEntries=[]
            block3D, blockIn = None,None
            for i in range(nEntries):
                if -1 == fid.seek(nextEntryOffset, 1):
                    #print('Error: the file specified is corrupted.')
                    #return None, None
                    raise IOError('Error: the file specified is corrupted.')

                blockInfo=struct.unpack('IIii', fid.read(4 * 4))
                BI={"Type"   : blockInfo[0],
                    "Format" : blockInfo[1],
                    "Offset" : blockInfo[2],
                    "Size"   : blockInfo[3]}

                if   BI["Type"] == 14: blockIn = BI
                elif BI["Type"] == 5:  block3D = BI

                #tdfBlockEntries.append(BI)
                nextEntryOffset = 16 + 256

            if block3D is None or block3D["Format"] not in [1,2]:
                #print("3D marker data missing")
                raise Warning("3D marker data missing")

            if blockIn is None:
                #print("Analogue data missing")
                raise Warning("Analogue data missing")

            #print(fid.tell())
            return block3D, blockIn
        

    @staticmethod
    def get3Ddata(fileName, blockInfo):
        with open(fileName, 'rb') as fid:
            fid.seek(blockInfo['Offset'])

            nFrames, freq, startTime, nTracks = struct.unpack(
                'iifi', fid.read(4*4))

            D = np.array(struct.unpack('3f', fid.read(3 * 4)))

            R = np.array(struct.unpack('9f', fid.read(9 * 4))).reshape(3,3).T

            T = np.array(struct.unpack('3f', fid.read(3 * 4)))

            fid.seek(4, 1)

            if blockInfo["Format"] in [1,3]:
                print("this yes")
                nLinks,=struct.unpack('i',fid.read(4))
                fid.seek(4,1)
                links=np.array(struct.unpack('%ii'%(2*nLinks),fid.read(2*nLinks*4)))

            labels=[u""]*nTracks
            tracks=np.ones((nFrames, 3*nTracks))*np.nan

            if blockInfo["Format"] in [1, 2]:
                for trk in range(nTracks):
                    lbl=fid.read(256).decode("mbcs")
                    labels[trk]=str(lbl)
                    #print(labels[trk])
                    #print(fid.read(256))
                    nSegments, = struct.unpack('i',fid.read(4))
                    #print("nSegments "+str(nSegments))
                    fid.seek(4, 1)
                    segments=np.array(struct.unpack(
                        "%ii"%(2*nSegments), fid.read(2*nSegments*4))).reshape(nSegments,2).T
                    #print(segments)
                    for s in range(nSegments):
                        for f in range(segments[0,s], segments[0,s] + segments[1,s]):
                            tracks[f,3*(trk) : 3*(trk)+3] = struct.unpack('3f',fid.read(3*4))
            
            elif blockInfo["Format"] in [3, 4]:
                for trk in range(nTracks):
                    lbl=fid.read(256).decode("mbcs")
                    labels[trk]=str(lbl)
                    #tracks = (fread (fid,[3*nTracks,nFrames],'float32'))';
                    tracks=np.array(struct.unpack(
                            '%if'%3*nTracks*nFrames, 
                            fid.read(3*nTracks*nFrames*4))).reshape(nFrames,3*nTracks).T
                            
            print("done")
            return tracks, labels, freq, nFrames, startTime

    @staticmethod
    def getAnalogue(fileName, blockInfo):
        with open(fileName, 'rb') as fid:
            fid.seek(blockInfo['Offset'])

            nSignals, frequency, startTime, nSamples = struct.unpack('iifi', fid.read(4*4))

            gpMap = np.array(struct.unpack('%ih'%nSignals, fid.read(nSignals*2)))

            labels = [""]*nSignals
            gpData = np.nan * np.ones((nSignals, nSamples))

            if blockInfo['Format'] is 1:
                for e in range(nSignals):
                    label=fid.read(256).decode("mbcs")
                    labels[e]=label
                    nSegments, = struct.unpack('i',fid.read(4))
                    fid.seek(4, 1)
                    segments = np.array(struct.unpack(
                        "%ii" % (2 * nSegments), fid.read(2 * nSegments * 4))).reshape(nSegments, 2).T
                    for s in range(nSegments):
                        gpData[e, segments[0, s]: (segments[0, s] + segments[1, s])] = \
                            struct.unpack('%if'%segments[1, s],fid.read(segments[1, s]*4))

            elif blockInfo['Format'] is 2:
                for e in range(nSignals):
                    label = fid.read(256).decode("mbcs")
                    labels[e] = label
                for frm in range(nSamples):
                    for sign in range(nSignals):
                        gpData[sign, frm],=struct.unpack('f',fid.read(4))

            return gpData, labels, frequency, nSamples, startTime,gpMap

