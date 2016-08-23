"""
So, what's the basic idea of this project?

Stuff to think about:
- what i've already worked on, and how i felt about it
- new project ideas I have
- tools I have and want to explore further

* What i've already worked on, and how i felt about it
Scramble: Takes in a MIDI files and 'scrambles' it up, completely randomly.
Transformations include
	- Reverse: sounds awesome but a bit cliche and gets old after a bit...
	- Invert: create notes in previously silent spaces. Hmm
	- Rotate: Kinda disorienting
	- Syncopate: Cool, but would be cooler if it wasn't just trivial windowing
	- Embed: Cool idea, but usually blows up. Might still work if I put a cap of like 20ms on it...
	- TimeMult: Speed up / slow down
Useful stuff I can pull from this:
	- How to write MIDI using prettyMidi
	- Basic logic structure for decision making (including statistical feedback) was used for scramblaudio

Scrambaudio: Scramble but based on pre-recorded audio
Transformations include:
	- Reverse
	- Rotate
	- ScrambleChunks: finds the onset times and just scrambles it to hell. It sometimes repeats which is half fun half annoying AF
	- Syncopate: linear window for now
Useful stuff I can pull from this:
	- Using essentia.onset_times
	- Writing files with essentia, altho its mono right now and takes fcking forever to write to file (shouldnt take that long, tho...)

New Project Ideas I have:
	- Writing midi in weird sped up freaked out ways
	- Taking samples and maybe glueing them on top of each other from the way above-mentioned MIDI is layed out
	- Taking samples and gnargling them all up and glueing them back together. But not in random ways
	- A python web app that takes sounds and then u can tweek some parameters and it serves sound.  I wonder how hard it would be to stream that sound?
	- Machine learning ideas:
		Have a huge bank of samples.  Pour through them to cluster them in interesting ways, or do analysis of spectral features on all of them, can even save that analysis in a DB for speed. Then reorganize the sounds in spectral-ish ways.
		Imagine a song where its the same song thruout but the samples and sounds just change thruout, but the basic structure is all the same and so boring

What have I learned from IDEO that I can apply
	- fullstack flask stuff whatever thatll come later
	- prototype fast and often
	- Hypothesis: Speeding up and slowing down might be interesting
	- Hypothesis: placing odd time signatures (like a 7 part trill in a 4/4 beat) in otherwise normal songs might be cool
	- HMW take normal boring sounds and recombine them in interesting ways to create a compelling music experience
"""
import copy, math, os, random, string

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

def fastMIDITrills():
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

def fastSampleTrills():
	"""
	Use the MIDI from fast midi trills, and just place and glue samples over it
	for each note in midiTrill:
		grab a random samples
		grab that length of that sample and shove it in there
	"""
	fs = 44100
	samplesDir = '/Users/mendelbot/Downloads/jazzy_chill_out/one_shot_drums/'
	allSamples = os.listdir(samplesDir)
	files = {}

	finalTrack = np.empty([1,1])

	for sample in allSamples:
		currFile = essentia.standard.MonoLoader(filename=samplesDir + sample)()
		files[sample] = currFile

	track, trackName = fastMIDITrills()

	for note in track.notes:
		length = note.end - note.start

		randomFileName = files.keys()[int(random.random()*len(files.keys()))]

		randomFile = files[randomFileName]
		numSamples = int(fs * length)

		thisSample = randomFile[0:numSamples]
		if random.random() < .3:
			thisSample = reverse(thisSample)

		finalTrack = np.append(finalTrack, thisSample)

		if note.end * fs > len(finalTrack):
			howBehind = int(note.end * fs - len(finalTrack))
	
			if howBehind > 0:
				zeros = [0] * howBehind
				finalTrack = np.append(finalTrack, zeros)

	print "Writing wav track"
	essentia.standard.MonoWriter(filename="outputs/%s.wav" % trackName, format="wav")(essentia.array(finalTrack)) # this shit takes forever ;(
	print "w00t! done"





def run():
	#fastMIDITrills()
	fastSampleTrills()

if __name__ == "__main__":
    run()