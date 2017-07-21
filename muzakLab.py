"""
Right now, generates a random MIDI pattern and randomly overlays samples onto it, writes a .wav file
"""
import copy, math, os, random, string, sys

import essentia.standard, numpy as np, pretty_midi as pm

"""
notes = []
    
notes.append(pm.Note(velocity=90,pitch=53,start=1.,end=1.333))
"""

### UTILITY FUNCTIONS ###

def randomInt(max, min=0):
	return int(math.floor(random.random() * (max - min)) + min)

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

### EXPERIMENTS ###

def randomMidiTrills():
	outputFile = pm.PrettyMIDI()
	track = pm.Instrument(38, is_drum=True) # 38 Acoustic Snare

	initialLength = .2
	initialPitch = 95

	direction = "down"
	velocity = 128
	pitch = initialPitch
	start = 0
	length = initialLength

	for i in xrange(1000):
		if velocity <= 60:
			velocity = 128
		else:
			velocity -= randomInt(5)

		if pitch <= 35:
			direction = "up"
		elif pitch > initialPitch:
			direction = "down"

		if direction == "down":
			pitch -= randomInt(7,1)
		elif direction == "up":
			pitch += randomInt(4,1)

		if length <= .02:
			length = initialLength
		else:
			length *= random.gauss(1.0, .1)

		currNote = pm.Note(velocity=velocity, pitch=pitch, start=start, end=start+length)
		start += length

		track.notes.append(currNote)

	trackName = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10)) + ".mid"
	outputFile.instruments.append(track)
	outputFile.write("outputs/" + trackName)

	print "w00t! wrote %s" % trackName

	return (track, trackName)

def meteredMIDIBeat(bpm=140, beatsInMeasure=4, numMeasures=32):
	maxBPM = 180
	minBPM = 80
	onTheWayUp = True
	changeTheBPM = False
	
	outputMIDI = pm.PrettyMIDI()
	track = pm.Instrument(38, is_drum=True) # 38 Acoustic Snare

	oneBeat = 60.0 / bpm

	currTime = 0
	for measure in xrange(numMeasures):
		for beat in xrange(beatsInMeasure):
			prob = random.random()
			if prob < .3:
				pattern = 'xxxx'
			elif prob < .4:
				pattern = 'xx_x'
			elif prob < .5:
				pattern = 'x'
			elif prob < .79:
				pattern = 'xx'
			elif prob < .89:
				pattern = '_x_x'
			elif prob < .97:
				pattern = 'xxx'
			else:
				pattern = 'xxxxxxxxxxxxxxx'

			currNotes = generateNotes(currTime, currTime+oneBeat, pattern)
			track.notes.extend(currNotes)
			currTime += oneBeat

			if changeTheBPM:
				if bpm > maxBPM:
					onTheWayUp = False
				elif bpm < minBPM:
					onTheWayUp = True

				bpmVelocity = 2
				if onTheWayUp:
					bpm += bpmVelocity
				else:
					bpm -= bpmVelocity
				oneBeat = 60.0 / bpm

	trackName = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10)) + ".mid"
	outputMIDI.instruments.append(track)
	outputMIDI.write("outputs/" + trackName)

	print "w00t! wrote %s" % trackName

	return (track, trackName)

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

# samplesDir='/Users/mendelbot/Downloads/jazzy_chill_out/one_shot_drums/'
def importSamples(samplesDir='/Users/mendelbot/Muzak/python/muzakLab/samples/oneShots/'):
	# Returns a files array
	allSamples = os.listdir(samplesDir)
	files = {}

	for sample in allSamples:
		currFile = essentia.standard.MonoLoader(filename=samplesDir + sample)()
		files[sample] = currFile

	return files


def fastSampleTrills():
	"""
	Use the MIDI from fast midi trills, and just place and glue samples over it
	for each note in midiTrill:
		grab a random samples
		grab that length of that sample and shove it in there
	"""
	# Setup vars
	fs = 44100
	finalTrack = np.empty([1,1])

	# Get Samples
	files = importSamples()
	
	#Get MIDI to write
	track, trackName = randomMidiTrills()

	for note in track.notes:
		length = note.end - note.start

		randomFileName = files.keys()[int(random.random()*len(files.keys()))]

		randomFile = files[randomFileName]
		numSamples = int(fs * length)

		thisSample = randomFile[0:numSamples]
		if random.random() < .3:
			thisSample = reverse(thisSample)

		finalTrack = np.append(finalTrack, thisSample)

		# If we're falling behind on samples, pad with some zeroes
		if note.end * fs > len(finalTrack):
			howBehind = int(note.end * fs - len(finalTrack))
	
			if howBehind > 0:
				zeros = [0] * howBehind
				finalTrack = np.append(finalTrack, zeros)

	print "Writing wav track"
	essentia.standard.MonoWriter(filename="outputs/%s.wav" % trackName, format="wav")(essentia.array(finalTrack)) # this shit takes forever ;(
	print "w00t! done"

def moreRhythmicSamples():
	
	if len(sys.argv) == 2:
		bpm = int(sys.argv[1])
	else:
		bpm = 140

	fs = 44100
	finalTrack = np.empty([1,1])

	# Get Samples
	files = importSamples()
	
	#Get MIDI to write
	track, trackName = meteredMIDIBeat(bpm=bpm)

	for note in track.notes:
		length = note.end - note.start

		randomFileName = files.keys()[int(random.random()*len(files.keys()))]

		randomFile = files[randomFileName]
		numSamples = int(fs * length)

		thisSample = randomFile[0:numSamples]
		if random.random() < .16:
			thisSample = reverse(thisSample)

		finalTrack = np.append(finalTrack, thisSample)

		# If we're falling behind on samples, pad with some zeroes
		if note.end * fs > len(finalTrack):
			howBehind = int(note.end * fs - len(finalTrack))
	
			if howBehind > 0:
				zeros = [0] * howBehind
				finalTrack = np.append(finalTrack, zeros)

	print "Writing wav track"
	essentia.standard.MonoWriter(filename="outputs/%s.wav" % trackName, format="wav")(essentia.array(finalTrack)) # this shit takes forever ;(
	print "w00t! done"

def run():
	#randomMidiTrills()
	#fastSampleTrills()
	moreRhythmicSamples()

if __name__ == "__main__":
    run()