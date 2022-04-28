import torch.nn as nn
import torch.nn.functional as F


class DQN2d(nn.Module):
    def __init__(self, state_dim, outputs):  # 13, 2, 34
        super(DQN2d, self).__init__()
        self.conv1 = nn.Conv1d(state_dim, 256, kernel_size=2, stride=2)
        self.bn1 = nn.BatchNorm1d(256)
        self.conv2 = nn.Conv1d(256, 256, kernel_size=2, stride=2)
        self.bn2 = nn.BatchNorm1d(256)
        self.head = nn.Linear(768, outputs)
        self.softmax = nn.Softmax()

    def forward(self, x):

        # x = self.pe(x)
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = self.head(x.view(x.shape[0], x.shape[1] * x.shape[2]))
        x = self.softmax(x)
        return x  # self.head(x)

