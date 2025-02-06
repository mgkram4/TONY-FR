import os
import random

import joblib
import numpy as np
from flask import Flask, jsonify, render_template, request
from sklearn.svm import SVC

app = Flask(__name__)

# Initialize the SVM model
model = SVC(kernel='rbf', C=1.0, probability=True)
X_train = []
y_train = []

MODEL_FILE = 'tictactoe_model.joblib'

# Load existing model if available
if os.path.exists(MODEL_FILE):
    model = joblib.load(MODEL_FILE)

def check_winner(board):
    winning_combinations = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
        [0, 4, 8], [2, 4, 6]  # Diagonals
    ]
    
    for combo in winning_combinations:
        if board[combo[0]] == board[combo[1]] == board[combo[2]] != '':
            return board[combo[0]], combo  # Return both winner and winning combination
    
    if '' not in board:
        return 'tie', None
    return None, None

def board_to_features(board):
    # Convert board to numerical features
    return [1 if x == 'X' else -1 if x == 'O' else 0 for x in board]

def get_winning_move(board, player):
    # Check if there's a winning move available
    for i in range(9):
        if board[i] == '':
            board_copy = board.copy()
            board_copy[i] = player
            if check_winner(board_copy) == player:
                return i
    return None

def get_ai_move(board):
    # Convert empty string to 0 for consistent processing
    numeric_board = [0 if x == '' else x for x in board]
    
    # First, check if AI can win in the next move
    winning_move = get_winning_move(board, 'O')
    if winning_move is not None:
        return winning_move
    
    # Then, check if we need to block player's winning move
    blocking_move = get_winning_move(board, 'X')
    if blocking_move is not None:
        return blocking_move
    
    # Get empty positions
    empty_positions = [i for i, x in enumerate(board) if x == '']
    
    if not empty_positions:
        return None
        
    # If model has been trained, use it to predict best move
    if len(X_train) > 10:  # Only use model after some training
        try:
            move_scores = {}
            for move in empty_positions:
                board_copy = numeric_board.copy()
                board_copy[move] = -1  # -1 represents 'O'
                prediction = model.predict_proba([board_to_features(board_copy)])
                move_scores[move] = prediction[0][1]  # Probability of winning
            
            # Choose the move with highest winning probability
            best_move = max(move_scores.items(), key=lambda x: x[1])[0]
            return best_move
        except:
            # Fallback to strategic moves if model prediction fails
            pass
    
    # Strategic moves if model isn't trained yet or prediction failed
    # Try to take center
    if 4 in empty_positions:
        return 4
    
    # Try to take corners
    corners = [pos for pos in [0, 2, 6, 8] if pos in empty_positions]
    if corners:
        return random.choice(corners)
    
    # Take any available edge
    edges = [pos for pos in [1, 3, 5, 7] if pos in empty_positions]
    if edges:
        return random.choice(edges)
    
    # Fallback to random move
    return random.choice(empty_positions)

def update_model(board, winner):
    global X_train, y_train, model
    
    # Convert board to features
    features = board_to_features(board)
    
    # Determine outcome (1 for O wins, 0 for X wins or tie)
    outcome = 1 if winner == 'O' else 0
    
    # Add to training data
    X_train.append(features)
    y_train.append(outcome)
    
    # Retrain model if we have enough data
    if len(X_train) > 5:
        try:
            model.fit(X_train, y_train)
            # Save the model
            joblib.dump(model, MODEL_FILE)
        except:
            pass  # Handle any training errors gracefully

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/make_move', methods=['POST'])
def make_move():
    board = request.json['board']
    
    # Check if game is already won
    winner, winning_combo = check_winner(board)
    if winner:
        if winner != 'tie':
            update_model(board, winner)
        return jsonify({'status': 'game_over', 'winner': winner, 'winning_combo': winning_combo})
    
    # Make AI move
    ai_move = get_ai_move(board)
    
    if ai_move is not None:
        board[ai_move] = 'O'
        
        # Check if AI won
        winner, winning_combo = check_winner(board)
        if winner:
            update_model(board, winner)
        
        return jsonify({
            'move': ai_move,
            'status': 'game_over' if winner else 'continue',
            'winner': winner if winner else None,
            'winning_combo': winning_combo
        })
    
    return jsonify({
        'status': 'game_over',
        'winner': 'tie',
        'winning_combo': None
    })

if __name__ == '__main__':
    app.run(debug=True)