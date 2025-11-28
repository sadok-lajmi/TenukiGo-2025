#!/usr/bin/env python3
"""
Test script for Move Completion API

This script provides various ways to test the move completion endpoints:
1. Direct API testing with sample data
2. Manual board state input
3. Loading and testing the legacy AI model
"""

import requests
import json
import numpy as np

# Backend server URL - adjust if needed
BASE_URL = "http://localhost:8000"

def create_sample_board_states():
    """Create sample board states for testing."""
    # Empty board
    empty_board = [[0 for _ in range(19)] for _ in range(19)]
    
    # Simple board with a few moves
    simple_board = [[0 for _ in range(19)] for _ in range(19)]
    simple_board[3][3] = 1  # Black stone
    simple_board[3][4] = 2  # White stone
    simple_board[4][3] = 1  # Black stone
    
    # More complex board state
    complex_board = [[0 for _ in range(19)] for _ in range(19)]
    # Black stones
    complex_board[3][3] = 1
    complex_board[4][3] = 1
    complex_board[5][3] = 1
    complex_board[3][5] = 1
    complex_board[4][5] = 1
    
    # White stones  
    complex_board[3][4] = 2
    complex_board[4][4] = 2
    complex_board[5][4] = 2
    complex_board[3][6] = 2
    
    return {
        "empty": empty_board,
        "simple_initial": empty_board,
        "simple_final": simple_board,
        "complex_initial": simple_board,
        "complex_final": complex_board
    }

def test_completion_status():
    """Test the completion service status."""
    print("🔍 Testing completion service status...")
    try:
        response = requests.get(f"{BASE_URL}/completion/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Service Status:", json.dumps(data, indent=2))
            return True
        else:
            print(f"❌ Status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_load_legacy_model():
    """Test loading the legacy AI model."""
    print("\n🤖 Testing legacy model loading...")
    try:
        response = requests.post(f"{BASE_URL}/completion/load_legacy_model")
        data = response.json()
        print("Model loading result:", json.dumps(data, indent=2))
        return data.get("success", False)
    except Exception as e:
        print(f"❌ Error loading legacy model: {e}")
        return False

def test_algorithmic_completion(boards):
    """Test algorithmic move completion."""
    print("\n🔧 Testing algorithmic completion...")
    
    test_data = {
        "initial_board": json.dumps(boards["simple_initial"]),
        "final_board": json.dumps(boards["simple_final"]),
        "use_ai": False,
        "board_size": 19
    }
    
    try:
        response = requests.post(f"{BASE_URL}/completion/suggest", data=test_data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Algorithmic completion result:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error in algorithmic completion: {e}")
        return False

def test_ai_completion(boards):
    """Test AI-based move completion."""
    print("\n🧠 Testing AI completion...")
    
    test_data = {
        "initial_board": json.dumps(boards["simple_initial"]),
        "final_board": json.dumps(boards["simple_final"]),
        "use_ai": True,
        "board_size": 19
    }
    
    try:
        response = requests.post(f"{BASE_URL}/completion/suggest", data=test_data)
        if response.status_code == 200:
            result = response.json()
            print("✅ AI completion result:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"❌ Request failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error in AI completion: {e}")
        return False

def print_board_visual(board, title="Board"):
    """Print a visual representation of the board."""
    print(f"\n{title}:")
    print("  " + " ".join([chr(ord('A') + i) for i in range(19)]))
    for i, row in enumerate(board):
        line = f"{i+1:2d} "
        for cell in row:
            if cell == 0:
                line += "· "
            elif cell == 1:
                line += "● "  # Black stone
            elif cell == 2:
                line += "○ "  # White stone
        print(line)

def interactive_test():
    """Interactive testing interface."""
    print("\n🎮 Interactive Testing Mode")
    print("You can manually create board states and test completion.")
    
    boards = create_sample_board_states()
    
    while True:
        print("\n" + "="*50)
        print("Available test scenarios:")
        print("1. Empty → Simple (3 moves)")
        print("2. Simple → Complex (5 more moves)")
        print("3. Custom board input")
        print("4. Visual board display")
        print("5. Exit")
        
        choice = input("\nSelect option (1-5): ").strip()
        
        if choice == "1":
            print_board_visual(boards["simple_initial"], "Initial Board")
            print_board_visual(boards["simple_final"], "Final Board")
            test_algorithmic_completion({
                "simple_initial": boards["simple_initial"],
                "simple_final": boards["simple_final"]
            })
        
        elif choice == "2":
            print_board_visual(boards["complex_initial"], "Initial Board")
            print_board_visual(boards["complex_final"], "Final Board")
            test_algorithmic_completion({
                "simple_initial": boards["complex_initial"],
                "simple_final": boards["complex_final"]
            })
        
        elif choice == "3":
            print("Custom input not implemented in this demo.")
            print("You can modify the board states in create_sample_board_states()")
        
        elif choice == "4":
            print_board_visual(boards["simple_final"], "Sample Board with Stones")
        
        elif choice == "5":
            print("👋 Goodbye!")
            break
        
        else:
            print("Invalid choice. Please select 1-5.")

def run_all_tests():
    """Run all automated tests."""
    print("🚀 Starting Move Completion API Tests\n")
    
    # Test 1: Service Status
    if not test_completion_status():
        print("❌ Cannot proceed - service not available")
        return
    
    # Test 2: Create sample boards
    boards = create_sample_board_states()
    print("✅ Sample board states created")
    
    # Test 3: Algorithmic completion
    test_algorithmic_completion(boards)
    
    # Test 4: Try to load legacy model
    model_loaded = test_load_legacy_model()
    
    # Test 5: AI completion (only if model loaded)
    if model_loaded:
        test_ai_completion(boards)
    else:
        print("⚠️ Skipping AI completion test - no model loaded")
    
    print("\n" + "="*50)
    print("✅ All tests completed!")

def main():
    """Main function with menu."""
    print("Move Completion API Tester")
    print("=" * 30)
    
    while True:
        print("\nChoose testing mode:")
        print("1. Run all automated tests")
        print("2. Interactive testing")
        print("3. Exit")
        
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            run_all_tests()
        elif choice == "2":
            interactive_test()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1-3.")

if __name__ == "__main__":
    main()