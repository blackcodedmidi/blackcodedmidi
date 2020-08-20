#import the pyplot and wavfile modules 

import matplotlib.pyplot as plot
from scipy.io import wavfile

 

# Read the wav file (mono)

samplingFrequency, signalData = wavfile.read('reptiliana.wav')

 

# plot.subplot(212)

plot.axes().set_axis_off()
plot.transparent= True

plot.specgram(signalData,Fs=samplingFrequency)
# plot.xlabel('Time')
# plot.ylabel('Frequency')

 

# plot.savefig("hola.png")
plot.show()