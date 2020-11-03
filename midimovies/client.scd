//------------------------------------
// SETUP
//------------------------------------
(
// create the NetAddr
o = NetAddr.new("127.0.0.1", 1337);
// a function to write the song to file and send the refresh message
~sendSong = {
	f = File(PathName.new(thisProcess.nowExecutingPath).parentPath ++ "midi.txt","w");
	f.write(~song.asCompileString);
	f.close;
	o.sendMsg("/refresh", nil);
	nil;
};

)

//------------------------------------
// PLAYGROUND
//------------------------------------

// control player speed
o.sendMsg("/speed", 100);



// build and send a new song
(
var frames = 50;
var tpf = 64;
~song = [];
frames.do{|f|
	var frame = [];
	tpf.do{|t|
		1.do{|n|
			var note, channel, start, end, msg;
			//------------------------------------

			note = 40 + (t%2) + f;
			channel = t;
			start = t/tpf;
			end = t/tpf + 0.01;

			//------------------------------------
			msg = [f, channel.asInteger % 10, note.asInteger % 127, start%1, end%1, 'False', 'False'];
			frame = frame.add(msg);
		};
	};
	~song = ~song.add(frame);
};

~sendSong.value;
)
