# Philadelphia Voter Statistics By Ward and Division.

Produces a GeoJSON file containing voter registartion and turnout by division. Based on the 2015 primary election.

### Setup

For Mac OS and Linux, make sure python 3 and virtualenv are installed first, Google for system specific setup, then:

```sh
git clone git@github.com/awm33/phl-ward-divisions
cd phl-ward-divisions
virtualenv --python=python3 env
source env/bin/activate
pip install --requirement requirements.txt
```

### Running

```sh
python ward_voter_stats.py
```
