import pandas
from flask import Flask, request, jsonify
import joblib, os, pickle, hashlib, torch, time
import numpy as np
from defender.models import MalConvPlus, MalwareDetector
import hashlib
from src.extract.feature_extraction import extract_features

LOCAL_FILE_PATH=os.path.join(os.path.dirname(os.path.realpath(__file__)), "../data/sample/002ce0d28ec990aadbbc89df457189de37d8adaadc9c084b78eb7be9a9820c81.exe")

def create_app():
    """Create a Flask application."""
    app = Flask(__name__)

    @app.route("/hello", methods=["GET"])
    def hello():
        return "Hello, World!"

    @app.route("/", methods=["POST"])
    def handle_request():
        start_time = time.time()
        malware = 0

        if request.headers["Content-Type"] != "application/octet-stream":
            return jsonify({"error": "expecting application/octet-stream"}), 400

        data = request.get_data()
        print(f"Received {len(data)} bytes of data.")
        features_data, header = extract_features(data)
        # Use Ember to extract features
        # extractor = ember.PEFeatureExtractor()
        # features = extractor.feature_vector(data)
        # features = np.array(features).reshape(1, -1)

        predictions = []
        # load RF
        clf = joblib.load(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../models/malware_classifier_v2.joblib"))
        # load Malconv
        embed_dim = 8
        max_len = 4096
        out_channels = 128
        window_size = 32
        dropout = 0.5
        weight_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"../models/malconv_v2.pt")
        if torch.cuda.is_available():
            device = torch.device("cuda")
        else:
            device = torch.device("cpu")
        malconv = MalConvPlus(embed_dim, max_len, out_channels, window_size, dropout)
        malconv.load_state_dict(torch.load(weight_path))
        malconv.to(device)
        malconv.eval()
        #load RNN
        np.seterr(invalid='ignore')
        selected_features = [2379, 32, 683, 17, 596, 126, 106, 613, 626, 637, 164, 641, 592, 725]
        input_size = 14
        hidden_size = 64
        output_size = 2
        dl_model = MalwareDetector(input_size, hidden_size, output_size)
        dl_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"../models/malware_detector.pth")
        dl_model.load_state_dict(torch.load(dl_path))
        dl_model.eval()

        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"../models/scaler.pickle"), "rb") as f:
            mean, var = pickle.load(f)
            std = np.sqrt(var)
        try:
            features_data, header = extract_features(data)
        except:
            malware = 0
            predictions.append([0, 0, 0])
            end_time = time.time() 
            elapsed_time = end_time - start_time
            return jsonify({
            "malware": malware,
            "elapsed_time": elapsed_time,
            "predictions": predictions
            })
            # results.append([folder+"_"+file] + [folder] + [label] + [1.0, 0.0, 0.0])
        input = torch.tensor(header).unsqueeze(0).to(device)
        y_pred1 = clf.predict(features_data)
        with torch.no_grad():
            y_pred2 = torch.sigmoid(malconv(input))
            y_pred2 = (y_pred2 >= 0.5).int()
            features_data = (features_data-mean)/std
            selected = [features_data[0][selected_features]]
            # print(selected)
            features = torch.tensor(selected, dtype=torch.float32)
            y_pred3 = dl_model(features)
            # y_pred3 = torch.softmax(y_pred3, dim = -1)
            _, y_pred3 = torch.max(y_pred3, 1)

        # with torch.no_grad():
        #     features = torch.tensor(features, dtype=torch.float32)
        #     output = dl_model(features)
        #     _, predicted = torch.max(output, 1)
        predictions.append(y_pred1.item())
        predictions.append(y_pred2.item())
        predictions.append(y_pred3.item())
        # print(predictions)
        # Majority Voting
        if sum(predictions) >= 2:
            malware = 1
        
        end_time = time.time() 
        elapsed_time = end_time - start_time
        return jsonify({
            "malware": malware,
            "elapsed_time": elapsed_time,
            "predictions": predictions
        })
    
    @app.route("/model", methods=["GET"])
    def get_model():
        return jsonify({"model": "tbd"})

    return app
