import torch
import torch.nn as nn
import torch.nn.functional as F


class ClasswiseRegulatedEntropy(nn.Module):
    def __init__(self, C, K, device, psi=1e-7):
        assert K > 0 and type(K) is int, 'Hyper-parameter "alpha" should be a integer (> 0).'
        self.C = C                                                   # C (number of classes)
        self.K = K                                                   # K
        self.psi = psi                                               # ψ
        self.device = device                                         # {'cpu', 'cuda:0', 'cuda:1', ...}
        super(ClasswiseRegulatedEntropy, self).__init__()

    def forward(self, yHat, y):
        # [Pseudo code]
        # e = - (yHat / norm) log (yHat / norm)
        # e += - K * ( (ψ / norm) log (ψ / norm) )
        # e = e ⊙ (yHat + γ) (⊙: Hadamard Product)
        # e = e ⊙ yHat_zerohot (To ignore all ground truth classes)
        # e = scalar_sum(e)
        # e = e / N

        batch_size = len(y)                                          # N
        yHat = F.softmax(yHat, dim=1)
        # print('예찬 yHat', yHat.shape)
        psi_distribution = torch.ones_like(yHat) * self.psi
        # print('예찬 psi_distribution', psi_distribution.shape)
        yHat_zerohot = torch.ones(batch_size, self.C).scatter_(1, y.view(batch_size, 1).data.cpu(), 0)
        # print('예찬 yHat_zerohot', yHat_zerohot.shape)
        norm = yHat + psi_distribution * self.K + 1e-10
        # print('예찬 norm', norm.shape)
        classwise_entropy = (yHat / norm) * torch.log((yHat / norm) + 1e-10)
        # print('예찬 classwise_entropy', classwise_entropy.shape)
        classwise_entropy += ((psi_distribution / norm) * torch.log((psi_distribution / norm) + 1e-10)) * self.K
        # gamma = 0.3
        # classwise_entropy *= (yHat + gamma)
        classwise_entropy *= yHat_zerohot.to(device=self.device)
        entropy = float(torch.sum(classwise_entropy))
        # print('예찬 entropy', entropy.shape)
        entropy /= batch_size
        return entropy
