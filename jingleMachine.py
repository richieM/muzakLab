# Utility used by scramblaudio, mainly overlayAudioWithSamples

import copy, math, random, os, string, sys
import essentia.standard, pretty_midi as pm, numpy as np
SAMPLES_DIR = "/Users/mendelbot/Muzak/python/samples/"


def importSamples(samplesDir='/Users/mendelbot/Muzak/python/muzakLab/samples/oneShots/'):
	# Returns a files array
	print "importing"
	allSamples = os.listdir(samplesDir)
	files = {}

	for sample in allSamples:
		currFile = essentia.standard.MonoLoader(filename=samplesDir + sample)()
		files[sample] = currFile

	print "done importing"

	return files

def reverse(x):
    """ 
    Reverses a segment of audio.
    
    Args:
        x: 1D array
     
    Returns:
        a copy of X, reversaflippydipped
    """
    
    arr = copy.copy(x)
    
    length = len(arr)
    for i in range(length/2):
        temp = arr[i]
        arr[i] = arr[length-i-1]
        arr[length-i-1] = temp
    return arr

def overlayAudioWithSamples(fileName=None, audio=None, samples=None):
	"""
	Fill the space with some samples and math rock it...

	TODO -- use some of the stuff in scramblaudio, but just rewrite the uhhhhh Run file and just reuse everything else if i can
	"""

	### Generate some MIDI based on the inputs
	fs = 44100
	if fileName:
		x = essentia.standard.MonoLoader(filename=fileName)()
	else:
		x = essentia.array(audio)

	onsetTimes, onset_rate = essentia.standard.OnsetRate()(x)
	track = pm.Instrument(38, is_drum=True) # 38 Acoustic Snare
	trackName = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))

	print "** Generate some MIDI"

	for i in range(len(onsetTimes)-1):
		currOnset = onsetTimes[i]
		nextOnset = onsetTimes[i+1]
		beatSpace = nextOnset - currOnset

		rhythmPattern = chooseRandomRhythm()
		currNotes = generateNotes(currOnset, nextOnset, rhythmPattern)
		track.notes.extend(currNotes)

	print "** Assign random samples to the MIDI"
	finalTrack = np.empty([1,1])

	if samples is None:
		files = importSamples() # Get Samples

	for note in track.notes:
		length = note.end - note.start

		randomFileName = samples.keys()[int(random.random()*len(samples.keys()))]

		randomFile = samples[randomFileName]
		numSamples = int(fs * length)

		thisSample = randomFile[0:numSamples]
		if random.random() < .2:
			thisSample = reverse(thisSample)

		finalTrack = np.append(finalTrack, thisSample)

		# If we're falling behind on samples, pad with some zeroes
		if note.end * fs > len(finalTrack):
			howBehind = int(note.end * fs - len(finalTrack))
	
			if howBehind > 0:
				zeros = [0] * howBehind
				finalTrack = np.append(finalTrack, zeros)

	finalTrack = np.append(finalTrack, np.zeros(len(x) - len(finalTrack))) / 2.5 # quieter
	combinedTrack = np.add(x, finalTrack)

	print "Writing wav track"
	if fileName:
		essentia.standard.MonoWriter(filename="outputs/%s.wav" % trackName, format="wav")(essentia.array(combinedTrack)) # this shit takes forever ;(
	else:
		return combinedTrack
	print "w00t! done"
	print "trackName: %s" % trackName


def chooseRandomRhythm():
	prob = random.random()
	if prob < .5:
		pattern = 'x'
	elif prob < .67:
		pattern = 'xx'
	elif prob < .8:
		pattern = 'xxx'
	elif prob < .9:
		pattern = 'x_x_'
	elif prob < .95:
		pattern = 'xxxxxxx'
	else:
		pattern = 'xxxx'
	return pattern

def generateNotes(start, end, pattern):
	# pattern is an array of either 'x' or '_'
	noteLength = (end-start) / len(pattern)
	notes = []
	velocity = 100
	pitch = 80

	currTime = start

	for char in pattern:
		if char == 'x':
			currNote = pm.Note(velocity, pitch, start=currTime, end=currTime+noteLength)
			notes.append(currNote)
		currTime += noteLength

	return notes
	
if __name__ == "__main__":
	fileName = 'getting_jiggy_post.wav'
	scramblaudio = overlayAudioWithSamples(SAMPLES_DIR + fileName)
