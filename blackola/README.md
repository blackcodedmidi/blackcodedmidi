# midimovies

## Linux

To start Timidity in daemon mode:

```bash
timidity -iA
```

Now, you should see Timidity as ALSA virtual devices. Try running `aconnect
-o`:

```bash
aconnect -o
```

```
client 14: 'Midi Through' [type=kernel]
    0 'Midi Through Port-0'
client 129: 'TiMidity' [type=user,pid=32358]
    0 'TiMidity port 0 '
    1 'TiMidity port 1 '
    2 'TiMidity port 2 '
    3 'TiMidity port 3 '
```

To play a MIDI using the player, run:

```bash
midimovies_player.py output.mid
```

It will try to use the first output device found. You can specify another one using the `-o` option:

```bash
midimovies_player.py -o "TiMidity:TiMidity port 0 129:0" output.mid
```
