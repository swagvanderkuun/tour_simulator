# Tour de France Cycling Game Simulator

This simulator recreates the cycling game mechanics from scorito.nl for the Tour de France. It simulates 21 stages of the Tour de France, where riders' performances are determined by triangular probability distributions.

## Features
- Simulation of 21 Tour de France stages
- Rider database with performance probabilities
- Triangular distribution-based result generation
- Point calculation based on stage results

## Setup
1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the simulator:
```bash
python simulator.py
```

## Project Structure
- `simulator.py`: Main simulation logic
- `riders.py`: Rider database and probability distributions
- `requirements.txt`: Project dependencies 