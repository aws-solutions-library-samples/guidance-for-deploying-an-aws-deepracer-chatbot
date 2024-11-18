import json


def get_track_by_id(track_id):
    # open a local file using with open
    with open("./deepracer-tracks-v3.json") as f:
        tracks = json.load(f)
        for track in tracks:
            current_track_id = track["TrackArn"].split("/")[1]
            if current_track_id == track_id:
                return track
        return None


def get_track_meta_data():
    return {
        "TrackDifficulty": "Track difficulty is an integer ranging from 100 to 1, where 1 is the hardest",
        "TrackLength": "Meters",
        "TrackWidth": "Centimeters",
        "TrackUsageCount": "Number of times the track has been used",
    }
