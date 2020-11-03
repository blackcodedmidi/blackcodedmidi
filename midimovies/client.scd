//------------------------------------
// SETUP
//------------------------------------
(
// create the NetAddr
o = NetAddr.new("127.0.0.1", 1337);

~maxChannels = 10;
~maxNotes = 127;

// a function to write the song to file and send the refresh message
~sendSong = { |song|
	f = File(PathName.new(thisProcess.nowExecutingPath).parentPath ++ "midi.txt","w");
	f.write(song.asCompileString);
	f.close;
	o.sendMsg("/refresh", nil);
	nil;
};

// a function that creates and sends a song
// - tickFn: this function will be called for each tick and frame
//       expects a function with args: f (current frame), t (current tick in frame)
//       expects to return a list of [note, channel, duration]
// - frames: number of song frames (e.g. 64)
// - tpb: ticks per frame (resolution) (e.g. 64)
~updateSong = { |tickFunc, frames, tpf|
	var song = [];

	frames.do { |f|
		var frame = [];

		tpf.do { |t|
			var tickMsg, msg;
			var note, channel, duration;
			var start, end;

			tickMsg = tickFn.value(f, t);
			note = tickMsg[0];
			channel = tickMsg[1];
			duration = tickMsg[2];

			start = t / tpf;
			end = ((t + duration) / tpf) + 0.01;  // +0.01 ???

			msg = [
				f,
				channel.asInteger % ~maxChannels,
				note.asInteger % ~maxNotes,
				start % 1,
				end % 1,
				'False',
				'False'
			];

			frame = frame.add(msg);
		};

		song = song.add(frame);
	};

	~sendSong.(song);
}
)

//------------------------------------
// PLAYGROUND
//------------------------------------

// control player speed
o.sendMsg("/speed", 1);

// create a new song
(
~updateSong.({ |f, t|
	var note, chan, dur;
	note = 50 + (f*3) + (sin(t/10)*5) + sin(t/3) + (sin(t/8)*20);
	chan = t;
	dur = 1;
	[note, chan, dur]
}, 64, 64);
)