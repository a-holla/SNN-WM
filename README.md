# SNN-WM
Spiking Neural Networks for Visual Memory Consolidation

![image](https://github.com/mallard1707/SNN-WM/assets/74109054/1efb1ddb-a362-439d-b4be-d60c6c18c4ff)

This project attempted to implement the visuospatial sketchpad of working memory (a division of short term memory) using a network of spiking neurons.

The above schematic was proposed to mainly explain 3 top-level psychological phenomena using bottom-level networks of neurons:
1. Retention: Images exposed to the sensory memory linger in the working memory for a short while.
2. Recapitulation: When learnt images in the long term memory are recalled, they are sent to the visuospatial sketchpad of the working memory.
3. Interference: Exposing the network to a fresh sample while trying to recall a learnt image at the same time. (Scrapped in the circuit implementation since the actual phenomenon of interference quoted in literature is far more complicated.)

The long-term network learns using the spike-time dependent plasticity learning rule (STDP).

# Usage

1. snnmnist-supervised.ipynb implements the learning of the long-term network and the three experiments described above using the Brian2 library in Python
2. The folder SPICEckts contains the LTSpice schematics for the crossbar-array based analog circuits that implement the above network design. Owing to circuit simulation time constraints, STDP learning is not done through analog circuitry and the weights are instead transferred from step 1. Weights are ideally stored on NVM devices like RRAM or Spintronics but for simplicity, in the schematics they are modelled as fixed value resistors since no learning happens at the circuit level. The three experiments can be simulated using the file recapitulation_crossbar_run.ipynb (Replace the .net file with the experiment you want to run: retention_crossbar.net, recapitulation_crossbar.net and interference_crossbar.net).
3. Neuron activations of the working memory can be viewed as videos in the videos folder.
4. Details on the experiment protocol and explanation of the circuit components can be found in the BTP2-Thesis.

# Thesis and Remarks

The report explaining the project in much greater detail can be found in BTP2-Thesis.pdf. Unfortunately, it is unlikely this work will get published in its current state due to a lack of rigorous literature review on the exact behaviour of working memory. For example, the role of attentional mechanisms in WM are not addressed in the current model. It is unlikely that a model, however interesting it may be, attempting to explain three (relatively old) psychological phenomena, while ignoring the rest of the work done on the cognitive modeling side currently in literature. There are multiple avenues for future work: 1. Complete circuit simulation of the current model including learning of NVM synapses (attractive from a neuromorphic perspective)
2. More accurate/cutting-edge cognitive modeling (needs a large amount of literature review and ground-level work)

