from flask import Flask, request, jsonify, render_template
import os
import shutil
from pathlib import Path

app = Flask(__name__)

def get_folder_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

def copy_files(source, dest):
    try:
        # Verify paths exist
        if not os.path.exists(source) or not os.path.exists(dest):
            return {"status": "error", "message": "Invalid source or destination path"}

        # Get available space
        _, _, free_space = shutil.disk_usage(dest)
        
        # Copy non-DVD folders first
        for item in os.listdir(source):
            if item != "DVD":
                source_item = os.path.join(source, item)
                dest_item = os.path.join(dest, item)
                
                if os.path.isdir(source_item):
                    shutil.copytree(source_item, dest_item, dirs_exist_ok=True)
                else:
                    shutil.copy2(source_item, dest_item)

        # Handle DVD folder last
        dvd_source = os.path.join(source, "DVD")
        dvd_dest = os.path.join(dest, "DVD")
        
        if os.path.exists(dvd_source):
            os.makedirs(dvd_dest, exist_ok=True)
            remaining_space = shutil.disk_usage(dest)[2]
            
            copied_games = []
            skipped_games = []
            
            for game in os.listdir(dvd_source):
                game_path = os.path.join(dvd_source, game)
                game_size = get_folder_size(game_path) if os.path.isdir(game_path) else os.path.getsize(game_path)
                
                if game_size < remaining_space:
                    if os.path.isdir(game_path):
                        shutil.copytree(game_path, os.path.join(dvd_dest, game), dirs_exist_ok=True)
                    else:
                        shutil.copy2(game_path, dvd_dest)
                    remaining_space -= game_size
                    copied_games.append(game)
                else:
                    skipped_games.append(game)

            return {
                "status": "success",
                "copied_games": copied_games,
                "skipped_games": skipped_games
            }
                    
        return {"status": "success", "message": "Copy completed successfully"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/copy', methods=['POST'])
def start_copy():
    data = request.get_json()
    source = data.get('source')
    dest = data.get('dest')
    
    if not source or not dest:
        return jsonify({"status": "error", "message": "Source and destination paths are required"})
    
    result = copy_files(source, dest)
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)