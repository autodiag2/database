#!/usr/bin/python3
from decoder import ISO3779_Decoder

class VIN_decoder_test:
    
    def test(self):
        vins = [
            (2010,"VF1BB05CF26010203"), (2010,"VR7ACYHZKML019510"), 
            (2010,"VF7RD5FV8FL507366"), (2010,"JTMBF4DV4A5037027")
        ]
        for year, vin in vins:
            decoder = ISO3779_Decoder(year, vin)
            print(f"VIN: {vin}")
            decoder.dump()

if __name__ == "__main__":
    VIN_decoder_test().test()