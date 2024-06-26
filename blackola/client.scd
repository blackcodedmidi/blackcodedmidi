//------------------------------------
// SETUP
//------------------------------------
(
// create the NetAddr
o = NetAddr.new("127.0.0.1", 1337);

~maxChannels = 16;
~maxNotes = 127;

// a function to write the song to file and send the refresh message
~sendSong = { |song|
	f = File(PathName.new(thisProcess.nowExecutingPath).parentPath +/+ "songs" +/+ "livecoded.txt","w");
	f.write(song.asCompileString);
	f.close;
	o.sendMsg("/refresh", "livecoded");
	nil;
};

// a function that creates and sends a song
// - tickFn: this function will be called for each tick and frame
//       expects a function with args: f (current frame), t (current tick in frame)
//       expects to return a list of [note, channel, duration]
// - frames: number of song frames (e.g. 64)
// - tpb: ticks per frame (resolution) (e.g. 64)
// - npf: notes per tick (e.g. 4)
~updateSong = { |tickFn, frames, tpf, npt|
	var song = [];

	frames.do { |f|
		var frame = [];

		tpf.do { |t|
			npt.do{ |n|
				var tickMsg, msg;
				var note, channel, duration, velocity;
				var start, end;

				tickMsg = tickFn.value(f, t, n);
				note = tickMsg[0];
				channel = tickMsg[1];
				duration = tickMsg[2];
				velocity = tickMsg[3];

				start = t / tpf;
				end = ((t + duration) / tpf) + 0.01;  // +0.01 ???

				msg = [
					f,
					channel.asInteger % ~maxChannels,
					note.asInteger % ~maxNotes,
					velocity.clip(0, 127),
					start.clip(0, 1),
					end.clip(0, 2),
					'False',
					'False'
				];

				frame = frame.add(msg);
			};
		};

		song = song.add(frame);
	};

	~sendSong.(song);
}
)

//------------------------------------
// PLAYGROUND
//------------------------------------

// control player speed. -100 to 100
o.sendMsg("/speed", 0);
// second argument is tween-time between current speed and target speed
o.sendMsg("/speed", 1, 4);
// somewhat a master volume, from 0 to 1
o.sendMsg("/master", 0.8);
// directly load a song
o.sendMsg("/refresh", "init");
o.sendMsg("/refresh", "galaxian");
o.sendMsg("/refresh", "chihuahua");
// distort: 0 is none, 1 was the usual amount. It can be negative!
o.sendMsg("/distort", 0);
//set channel palette: 'rgb', 'hip', "1bit", 'cute', 'vapor', 'pure', 'cga', full list in blackola.py
o.sendMsg("/color", 'pure');
//toggle clean bg (0 for False, 1 for True)
o.sendMsg("/clean", 1);
// release ALL notes immediately
o.sendMsg("/panic");
// auto release ALL notes when updating song (0 for False, 1 for True)
o.sendMsg("/release", 1);


// create a new song and load it to the player
(
~updateSong.({ |f, t, n|
	var note, chan, dur, vel;
	note = 50 + (f*3) + (sin(t/10)*5) + sin(t/3) + (sin(t/8)*2);
	note = note + n;
	chan = 0;
	dur = 0.5;
	vel = 64;
	[note, chan, dur, vel]
}, 64, 64, 1);
)