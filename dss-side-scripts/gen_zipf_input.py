import numpy

class FileManager:
        def __init__(self):
                self.zipfcounter = 0
                self.zipfdist = numpy.random.zipf(1.2,5000) # list size 5000!!!!

        def get_zipf_filename(self):
                while (self.zipfdist[self.zipfcounter] > 200): # biggest file name 200.webm!!!!
                        self.zipfcounter = self.zipfcounter + 1
                filename = str(self.zipfdist[self.zipfcounter]) + ".webm"
                if (self.zipfcounter == 5000):
                        self.zipfconuter = 0
                self.zipfcounter = self.zipfcounter + 1
                return filename + "\n"

if __name__ == "__main__":
        name_handler = FileManager()
        fhandler = open("data.csv","w")
        for i in range(0,1000):
            print name_handler.get_zipf_filename()
            fhandler.write(name_handler.get_zipf_filename())
        fhandler.close()