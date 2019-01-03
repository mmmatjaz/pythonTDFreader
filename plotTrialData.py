from TDF import TDF

filePath=u"C:\\m\\grive\\work\\GAmocap\\btsGimuXs\\bts\\"
trial=TDF(fileName=filePath+"Trial11_M_R.tdf")

plt.gcf().clf()
plt.plot(trial.timeM,trial.markers)

plt.plot(trial.timeA,trial.analogue[0,:])