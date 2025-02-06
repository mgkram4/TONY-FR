let board = ['', '', '', '', '', '', '', '', ''];
let gameActive = true;

document.querySelectorAll('.cell').forEach(cell => {
    cell.addEventListener('click', handleCellClick);
});

document.getElementById('reset').addEventListener('click', resetGame);

function handleCellClick(event) {
    const index = event.target.getAttribute('data-index');
    
    if (board[index] !== '' || !gameActive) return;
    
    // Player move
    board[index] = 'X';
    event.target.textContent = 'X';
    
    // Make API call for AI move
    fetch('/make_move', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({board: board})
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'game_over') {
            gameActive = false;
            displayStatus(data.winner);
        } else {
            // Update board with AI move
            board[data.move] = 'O';
            document.querySelector(`[data-index="${data.move}"]`).textContent = 'O';
            
            if (data.status === 'game_over') {
                gameActive = false;
                displayStatus(data.winner);
            }
        }
    });
}

function displayStatus(winner) {
    const statusElement = document.getElementById('status');
    if (winner === 'tie') {
        statusElement.textContent = "It's a tie!";
    } else {
        statusElement.textContent = `${winner} wins!`;
    }
}

function resetGame() {
    board = ['', '', '', '', '', '', '', '', ''];
    gameActive = true;
    document.querySelectorAll('.cell').forEach(cell => {
        cell.textContent = '';
    });
    document.getElementById('status').textContent = '';
}

function handleGameResponse(response) {
    if (response.move !== undefined) {
        const cell = document.querySelector(`[data-index="${response.move}"]`);
        cell.textContent = 'O';
    }
    
    if (response.status === 'game_over') {
        if (response.winner === 'tie') {
            document.getElementById('status').textContent = "It's a tie!";
        } else {
            document.getElementById('status').textContent = `${response.winner} wins!`;
            // Highlight winning combination
            if (response.winning_combo) {
                response.winning_combo.forEach(index => {
                    document.querySelector(`[data-index="${index}"]`).classList.add('winner');
                });
            }
        }
        gameActive = false;
    }
} 