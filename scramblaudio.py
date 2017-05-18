import copy, numpy as np, random, string
import librosa, essentia.standard, pyo
import jingleMachine

# FUNCTIONS FOR MAKING DECISIONS
# via Larry Polansky / David Kant

# a basic (but flexible!) implementation of statistical feedback
# the default growth function is growth(count) = count**alpha for alpha=1
# number of elements is equal to length of the counts list

# (count * weight) ^ alpha

def wchoose(weights):
    '''
    returns index of choice from a weighted distribution
    '''
    break_points = np.cumsum(weights).tolist()
    index = random.random()*break_points[-1]
    return sum([bp<=index for bp in break_points])
    
def statchoose(weights, counts, alpha=1, dropdown=0):
    '''
    statistical feedback, returns index of choice and new weights
    '''
    growth = lambda count: count**float(alpha)                                      # exponential growth function
    reset = lambda count: float(dropdown)                                           # reset to dropdown when chosen
    probs = [w*growth(c) if c != 0 else w*reset(c) for w,c in zip(weights,counts)]  # compute probabilites
    probs = [p/sum(probs) for p in probs]                                           # and normalize them
    index = wchoose(probs)                                                          # choose
    counts = [c+1 if i != index else 0 for i,c in enumerate(counts)]                # update counts
    return index, counts, probs

"""
Transformations:
- Reverse(x)
- Rotate(x, fs, onsetTimes, numRotations)
- Syncopate(x, numSyncopations)
"""

def Reverse(x):
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


def Rotate(x, fs, numRotations):
    """
    Rotate audio by a number of onset times.
    
    Args:
        x: input signal
        fs: sampling freq
        numRotations: desired num of rotations
    
    Returns:
        y: new rotated signal
    """  
    
    
    find_onsets = essentia.standard.OnsetRate()
    onsetTimes, onset_rate = find_onsets(x)
    
    print "Onset Times: %d" % len(onsetTimes)
    
    if len(onsetTimes) == 0:
        return x
    
    onsetTimeCutOff = len(onsetTimes) - numRotations
    if onsetTimeCutOff < 0:
        onsetTimeCutOff = len(onsetTimes) - 1
    
    print len(onsetTimes)
    cutTime = onsetTimes[onsetTimeCutOff]
    cutSample = int(cutTime * fs)
    # import pdb; pdb.set_trace()
    y = np.append(x[cutSample:], x[:cutSample])
    
    return y

def ScrambleChunks(x, fs):
    """
    Just take all the onset points and scramble the fuck out of it.
    Alternately, how about a probability in here to uh reverse and syncopate some of the chunks?
    
    Args:
        x: input signal
        fs: sampling freq
        
    Returns:
        y: new rotated signal
    """
    find_onsets = essentia.standard.OnsetRate()
    onsetTimes, onset_rate = find_onsets(x)
    
    print "Onset Times: %d" % len(onsetTimes)
    
    if len(onsetTimes) == 0:
        print "no onset times ;("
        return x
    
    arrayIndices = set(range(len(onsetTimes)))
    y = np.empty([1,1])
    
    while arrayIndices:
        currChunk = random.sample(arrayIndices,1)[0]
        arrayIndices.remove(currChunk)
        
        startTime = int(onsetTimes[currChunk] * fs)
        if currChunk == (len(onsetTimes) - 1):
            endTime = len(x) - 1
        else:
            endTime = int(onsetTimes[currChunk+1] * fs)
        
        currAudio = _Window(x[startTime:endTime])
        
        if (len(currAudio) < .13 * fs) and (len(currAudio) > .01 * fs) and (random.random() > 2): # TODO disabled for now
            import pdb; pdb.set_trace()
            numRepeats = int(random.random() * 7)
            print "REPEATING WTF"
            for _ in xrange(numRepeats):
                y = np.append(y, currAudio)
        else:
            if random.random() < .3:
                currAudio = Reverse(currAudio)

            y = np.append(y, currAudio)
    
    return y
                

def Syncopate(x, fs, numSyncopations):
    """
    Syncopate a signal by just windowing.
    
    Args:
        x: the chunk of audio to syncopate
        fs: sampling freq
        numSyncopations: number of chunks to syncopate
    
    Returns:
        y: new syncopated signal
        
    TODO: This is maybe clipping if the length of x is too small....
    so if x is smaller than a certain value, just return x
    """
    
    if len(x) > (fs * .05): 
        chunkLength = (int) (len(x) / numSyncopations)
        y = np.empty([1,1])
        chunkStart = 0
        for _unused in xrange(numSyncopations):
            newChunk = _Window(x[chunkStart:chunkStart+chunkLength])
            y = np.append(y, newChunk) #there will be a random 0 at the beginnign from the np.empty ;(
        return y
    else:
        return x


def _Window(x):
    """
    TODO: Make cooler windows -- exponential, etc. Linear is smelly
    Window the signal by fading in and out at ends.
    
    Questions:
        - what type of windowing? linear? exponential?
        - should the ramp time be constant or a function of the chunk length?
        
    Args:
        x: signal to be windowed
    
    Returns:
        y: windowed signal, yo.
    """
    RAMP_FACTOR = .02
    rampLength = _GetLinearRamp(x, RAMP_FACTOR)
    
    ramp = np.arange(0,1,1./rampLength)
    y = np.copy(x)
    
    for i in xrange(rampLength):
        y[i] = y[i] * ramp[i]
        y[len(x) - i - 1] = y[len(x) - i - 1] * ramp[i]
        
    return y


def _GetLinearRamp(x, RAMP_FACTOR):
    return (int) (len(x) * RAMP_FACTOR)


def _GetExponentialRamp(x, RAMP_FACTOR):
    # TODO
    pass
    

def Reverb(x):
    #TODO
    pass


def Run(theFile):
    """
    Perform random-ish transformations on an audio signal.
    
    Read in an audio signal, and then perform weightedly random transformations on that audio signal.
    Transformations are dependent, so the output of the last transformation becomes the input
    for the next transformation.
    
    Args:
        - theFile: name of audio file, read in as mono to avoid channel nausea
    """
    fs = 44100
    x = essentia.standard.MonoLoader(filename=theFile)()
    find_onsets = essentia.standard.OnsetRate()

    samples = jingleMachine.importSamples()
    
    numRuns = 15
    numTracks = 2
    tracks = [essentia.array(0) for i in range(numTracks)]
    
    # Statistical feedback setup
    alpha_statFeedback = 5
    weights = [3, # 0 Reverse
               2, # 1 Rotate
               0, # 2 Syncopate 4
               0, # 3 Syncopate 7
               3, # 4 ScrambleChunks
               0] # 5 Syncopate 17
               
    numXforms = len(weights)
    
    eventChoices = [[] for i in range(numTracks)] # empty list for each elem
    counts = [[1]*numXforms for i in range(numTracks)]
    
    for n in range(numTracks): # for each track
        for i in range(numRuns): # for each run
            choice, counts[n], unused_probs = statchoose(weights, counts[n], alpha=alpha_statFeedback)
            eventChoices[n].append(choice)
    # End statfeedback setup
    
    seedRhythms = [copy.copy(x) for i in range(numTracks)]
    for track, choices, seed, i in zip(tracks, eventChoices, seedRhythms, range(numTracks)):
        print "Calculating Track %d" % (i+1)
        tracks[i] = np.append(tracks[i], jingleMachine.mathRockJingle(audio=seed, samples=samples))
        for choice in choices:
            if choice == 0:
                # Reverse(x)
                print "Reverse"
                transAudio = Reverse(seed)
            elif choice == 1:
                # Rotate(x, fs, numRotations)
                print "Rotate"
                numRotations = 2
                transAudio = Rotate(seed, fs, numRotations)
            elif choice == 2:
                # Syncopate(x, 4)
                print "Syncopate 4"
                transAudio = Syncopate(seed, fs, 4)
            elif choice == 3:
                # Syncopate(x, 7)
                print "Syncopate 7"
                transAudio = Syncopate(seed, fs, 7)
            elif choice == 4:
                # Scramble it up! via chunks
                print "ScrambleChunks"
                transAudio = ScrambleChunks(seed, fs)
            elif choice == 5:
                # Scramble it up! via chunks
                print "Syncopate 17"
                transAudio = Syncopate(seed, fs, 3)
            
            combinedTrack = jingleMachine.mathRockJingle(audio=transAudio, samples=samples)

            tracks[i] = np.append(tracks[i], combinedTrack)
            seed = essentia.array(transAudio)
    
    # TODO ugly hack, doesn't work with numTracks, and SO SLOW
    print "All done! meowmeow <3"
    scramblaudio = [sum(x) for x in zip(tracks[0])]
    
    print "converted to weird summed array"
    
    trackName = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    
    print "writing file: %s" % trackName
    
    essentia.standard.MonoWriter(filename="outputs/%s.wav" % trackName, format="wav")(scramblaudio) # this shit takes forever ;(s
    return scramblaudio


if __name__ == "__main__":
	fileName = '/Users/mendelbot/Muzak/python/samples/berlin_everything.wav'
	scramblaudio = Run(fileName)
