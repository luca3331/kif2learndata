import torch
import torch.nn as nn
import numpy as np
import pandas as pd
from pfen2kifdata import InputData

class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.relu = nn.ReLU()

        self.conv1 = nn.Conv2d(in_channels=6, out_channels=16, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(in_channels=16, out_channels=32, kernel_size=3, padding=1)

        self.fc1 = nn.Linear(32 * 12 * 6 + 30, 1024)
        self.fc2 = nn.Linear(1024, 22)

    def forward(self, field, others):
        x = self.conv1(field)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.relu(x)
        x = x.view(x.size()[0], -1)
        x = torch.cat([x, others], dim=1)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

def main():
    model_path = './_model/model.pth'
    model = Net()
    model_dict = torch.load(model_path)
    model.load_state_dict(model_dict)
    model.eval()

    command = 'position gggb/ppbgg/gpb//// 6 gggbpp/bp/gggb//// 6 0 0 0'
    tumos = 'tumo gg gb pp gb pg gb br gp rp bp bp pg br gr gr pr bg pb pp pg gp pr br rr pr bg gg bp rr rr pp gg br bp bb gb rr rb pb rg gr rp br br pp pp gg rp gg rg pb bp pb pg pg bp rp gr bg pb bb bg gp bg pp rr gp rg br bp bp pp pr rp bp br pg bb rr bp gp pb gb pr rb pr pg pp rp rp rb gb br pg gp br pp pb pr pb rp rg pp gg rp rg gb bp pp pb pp gp gb pr pb bg bb bg gp rp gg rg gp gr rp pg gb pb'
    tmp = InputData(command, tumos.split(' ')[1:])

    with torch.no_grad():
        x1 = torch.tensor(tmp.encoded_field).view(6, 12, 6)
        outputs = model(x1, torch.tensor(tmp.encoded_others))
        predict = torch.softmax(outputs, dim=1)



if __name__ == "__main__":
    main()