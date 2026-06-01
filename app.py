import os
import json
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
# Note: In a real scenario with actual TCAD data, we would use mlfompy's ML module
# to load the fds (MLFoMpy Dataset) and predict the I-V characteristics.
# Since we don't have raw TCAD .plt/.csv files, we will simulate the ML model backend
# returning the I-V curves.

app = Flask(__name__)
CORS(app)

print("Starting MLFoMpy Backend Server...")

def simulate_mlfompy_prediction(params):
    """
    This function simulates what MLFoMpy's ML module would do:
    It takes the device parameters and predicts the full I-V curves and FoMs.
    """
    Lg = float(params.get('Lg', 12))
    Wns = float(params.get('Wns', 20))
    Nstacks = float(params.get('Nstacks', 3))
    T_c = float(params.get('T', 25))
    Vdd = float(params.get('Vdd', 0.7))
    Nch = float(params.get('Nch', 1e16))
    
    # Physics constants
    q = 1.6e-19
    kT = 1.38e-23 * (T_c + 273.15)
    Vt = kT / q
    
    # Simple predictive surrogate model (approximating MLFoMpy inference)
    Vth = 0.35 - 0.001 * (T_c - 25) - 0.01 * (Lg - 12) + 0.005 * np.log10(Nch/1e16)
    SS = 60 * ((T_c + 273.15) / 300) * (1 + 10 / Lg)
    DIBL = 20 * (12 / Lg)
    
    # Generate Transfer Characteristic (Id - Vgs)
    vgs_array = np.linspace(0, Vdd, 20)
    id_transfer = []
    for vgs in vgs_array:
        if vgs < Vth:
            # Subthreshold
            current = 1e-12 * 10 ** ((vgs - Vth) / (SS / 1000))
        else:
            # Strong inversion
            current = 1e-6 * (Wns / Lg) * Nstacks * ((vgs - Vth) ** 1.5)
        id_transfer.append(float(current))
        
    Ion = id_transfer[-1]
    Ioff = id_transfer[0]
    
    # Generate Output Characteristic (Id - Vds) for Vgs = Vdd
    vds_array = np.linspace(0, Vdd, 20)
    id_output = []
    for vds in vds_array:
        current = Ion * (1 - np.exp(-vds / 0.1)) * (1 + 0.05 * vds)
        id_output.append(float(current))
        
    return {
        "foms": {
            "Vth": float(Vth),
            "SS": float(SS),
            "DIBL": float(DIBL),
            "Ion": float(Ion),
            "Ioff": float(Ioff),
            "muEff": 250.0 - 0.5 * (T_c - 25)
        },
        "curves": {
            "transfer": {
                "vgs": vgs_array.tolist(),
                "id": id_transfer
            },
            "output": {
                "vds": vds_array.tolist(),
                "id": id_output
            }
        }
    }

@app.route('/api/predict', methods=['POST'])
def predict():
    params = request.json
    try:
        result = simulate_mlfompy_prediction(params)
        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    # Run the Flask API on port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)
