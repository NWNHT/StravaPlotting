# Cache class for use with strava but with slight modifications could likely be applied to other data

from datetime import date
import os


class Cache:
    def __init__(self, dir = None):
        if dir is None:
            # This assumes directory structure as used for Strava git directory
            self.dir = os.getcwd() + "/../stream_cache/"
        else:
            self.dir = dir
        # self.dir = "/Users/lucasnieuwenhout/Documents/Programming/Python/Projects/Strava/stream_cache/"
        self.contents = self.get_contents()

    def get_contents(self) -> set:
        """Read the contents of the specified directory and save the name of all .txt files."""
        return {x for x in os.listdir(self.dir) if x.endswith(".txt")}

    def cache_contains(self, activ_id: int) -> str | None:
        """Check if the cache contains a record for a given id, return filename if so, else return None."""
        for filename in self.contents:
            if filename.startswith(str(activ_id)):
                return filename
        return None

    def date_of_cache_entry(self, activ_id: int) -> date | None:
        """Return date of cache record by given id if it exists, else return None."""
        # If the cache does not contain the file, return None
        filename = self.cache_contains(activ_id)
        if filename is None:
            return None

        return date.fromisoformat(filename.split('_')[1].split('.')[0])
        
    def retrieve_stream(self, activ_id: int) -> str | None:
        """Retrieve a cache record in text if it exists, else return None."""
        # If the cache does not contain the file, return None
        filename = self.cache_contains(activ_id)
        if filename is None:
            return None
        
        # Read and return file
        with open(self.dir + filename, "r") as fh:
            return fh.read(1000000)

    def cache_json(self, activ_id: int, text: bytes):
        """Create a record in the cache for the given id, containing the given text. This will delete any existing records with given id.
        - This takes in a byte object and writes a string to the cache"""
        # If there is already with that file id, delete it and remove from contents list
        potential_existing_file = self.cache_contains(activ_id)
        if potential_existing_file:
            os.remove(self.dir + potential_existing_file)
            self.contents.remove(potential_existing_file)

        # Construct file name, add file name to contents list
        filename = f"{activ_id}_{date.today().isoformat()}.txt"
        self.contents.add(filename)
        with open(self.dir + filename, "w") as fh:
            fh.write(str(text)[2:-1])
    
    def clean_cache(self):
        """Clean any old records from the cache. Theoretically this shouldn't be required as the other methods are consistent but who know what can happen."""
        existing = {}
        for file in os.listdir(self.dir):
            file_id = file.split("_")[0]
            file_date = file.split('_')[1].split('.')[0]
            # If the file_id has already been read
            if file_id in existing:
                # If the newly read file has a greater/newer date, delete previous file, update existing dictionary, else delete the newly found file
                if date.fromisoformat(file_date) > date.fromisoformat(existing[file_id]):
                    os.remove(self.dir + str(file_id) + "_" + existing[file_id] + ".json")
                    existing[file_id] = file_date
                else:
                    os.remove(self.dir + file)
            else:  # If id has not already been read just add to record
                existing[file_id] = file_date
        # Update the contents set after all repeated records have been removed
        self.contents = self.get_contents()
