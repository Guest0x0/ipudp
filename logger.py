
import sys
import time

class Logger:
    def __init__(self, freq, target=sys.stdout):
        self.freq = freq
        self.target = target
        self.timestamp = time.time()
        self.in_traffic = { 'g': 0, 'm': 0, 'k': 0, 'b': 0 }
        self.out_traffic = { 'g': 0, 'm': 0, 'k': 0, 'b': 0 }

    def log(self, msg):
        print(msg, file=self.target)

    def log_traffic(self):
        new_time = time.time()
        if new_time - self.timestamp > self.freq:
            for (label, traffic) in [ ('in:', self.in_traffic), ('out:', self.out_traffic) ]:
                for measure in [ 'g', 'm', 'k', 'b' ]:
                    if traffic[measure] > 0:
                        if measure == 'g':
                            print(label, traffic['g'], "g", traffic['m'], "m", file=self.target)
                        else:
                            print(label, traffic[measure], measure, file=self.target)
                        break
                    elif measure == 'b':
                        print(label, traffic['b'], "b")
            self.timestamp = new_time

    def add_traffic(self, mode, size):
        if mode == 'i':
            traffic = self.in_traffic
        elif mode == 'o':
            traffic = self.out_traffic
        else:
            raise Exception("unknown mode " + mode)

        traffic['b'] = traffic['b'] + size
        for (small, big) in [ ('b', 'k'), ('k', 'm'), ('m', 'g') ]:
            if traffic[small] > 1024:
                traffic[big] = traffic[big] + traffic[small] // 1024
                traffic[small] = traffic[small] % 1024
            else:
                break
        self.log_traffic()
