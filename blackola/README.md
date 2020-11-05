# midimovies

## Install

### Linux

Create virtualenv and activate it

```
virtualenv .venv
source .venv/bin/activate
```

Now install dependencies:

```
sudo apt install rtmidi timidity
pip install -r requirements.txt
```

## Usage

### Linux

To start Timidity, run in a separate terminal:

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

To start Blackola and connect it to TiMidity, run:

```bash
python blackola.py -o 'TiMidity port 0'
```
