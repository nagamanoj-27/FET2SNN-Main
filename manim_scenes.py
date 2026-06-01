from manim import *

class BiologicalNeuron(Scene):
    def construct(self):
        # 1. Title
        title = Text("Biological Neuron: Integrate & Fire").scale(0.9).to_edge(UP)
        self.play(Write(title))

        # 2. Draw Neuron Components
        # Soma (Cell Body)
        soma = Circle(radius=1.2, color=BLUE, fill_opacity=0.3)
        soma_label = Text("Soma\n(Integration)").scale(0.5).move_to(soma.get_center())
        
        # Axon
        axon = Line(start=soma.get_right(), end=RIGHT * 5, color=WHITE, stroke_width=6)
        axon_label = Text("Axon (Output)").scale(0.5).next_to(axon, UP)

        # Dendrites
        dendrite_lines = [
            Line(start=LEFT * 5 + UP * 2, end=soma.get_left() + UP * 0.5, color=WHITE, stroke_width=4),
            Line(start=LEFT * 5, end=soma.get_left(), color=WHITE, stroke_width=4),
            Line(start=LEFT * 5 + DOWN * 2, end=soma.get_left() + DOWN * 0.5, color=WHITE, stroke_width=4)
        ]
        dendrite_label = Text("Dendrites (Inputs)").scale(0.5).next_to(dendrite_lines[0], UP, buff=0.2)

        self.play(
            Create(soma), Write(soma_label),
            *[Create(d) for d in dendrite_lines], Write(dendrite_label),
            Create(axon), Write(axon_label)
        )
        self.wait(1)

        # 3. Incoming Spikes (Neurotransmitters)
        spikes = []
        for d in dendrite_lines:
            spike = Dot(color=YELLOW).move_to(d.get_start())
            spikes.append(spike)
        
        # Animate spikes traveling to soma
        self.play(
            *[MoveAlongPath(spike, line) for spike, line in zip(spikes, dendrite_lines)],
            run_time=2, rate_func=linear
        )
        self.play(*[FadeOut(spike) for spike in spikes])

        # 4. Soma Integration (Membrane Potential Rising)
        charging_text = Text("Membrane Potential Rising...").scale(0.5).next_to(soma, DOWN)
        self.play(Write(charging_text))
        
        self.play(soma.animate.set_fill(RED, opacity=0.8), run_time=1.5)
        
        threshold_text = Text("Threshold Reached!").scale(0.6).next_to(soma, DOWN).set_color(RED)
        self.play(Transform(charging_text, threshold_text))
        
        # 5. Action Potential (Firing)
        action_potential = Dot(color=YELLOW, radius=0.15).move_to(axon.get_start())
        self.play(FadeIn(action_potential))
        self.play(
            MoveAlongPath(action_potential, axon),
            soma.animate.set_fill(BLUE, opacity=0.3), # Reset soma
            run_time=0.5, rate_func=rush_into
        )
        self.play(FadeOut(action_potential), FadeOut(charging_text))
        
        self.wait(2)


class TransistorSNN(Scene):
    def construct(self):
        # 1. Title
        title = Text("Transistor as a Leaky Integrate & Fire Neuron").scale(0.8).to_edge(UP)
        self.play(Write(title))

        # 2. Draw Transistor (MOSFET/NSFET abstract representation)
        # Channel
        channel = Rectangle(width=3, height=0.5, color=BLUE, fill_opacity=0.3)
        channel_label = Text("Channel").scale(0.5).move_to(channel.get_center())
        
        # Gate
        gate = Rectangle(width=2.5, height=0.3, color=GRAY, fill_opacity=0.8).next_to(channel, UP, buff=0.1)
        gate_label = Text("Gate (Input / Dendrite)").scale(0.4).move_to(gate.get_center())
        
        # Source & Drain
        source = Rectangle(width=1, height=0.5, color=GREEN, fill_opacity=0.5).next_to(channel, LEFT, buff=0)
        source_label = Text("Source").scale(0.4).move_to(source.get_center())
        
        drain = Rectangle(width=1, height=0.5, color=GREEN, fill_opacity=0.5).next_to(channel, RIGHT, buff=0)
        drain_label = Text("Drain (Output / Axon)").scale(0.4).move_to(drain.get_center())

        transistor_group = VGroup(channel, channel_label, gate, gate_label, source, source_label, drain, drain_label)
        transistor_group.move_to(DOWN * 0.5)

        self.play(Create(transistor_group))
        self.wait(1)

        # 3. Input Spikes arriving at Gate
        spike_in = Dot(color=YELLOW).move_to(gate.get_top() + UP * 2)
        arrow_in = Arrow(start=spike_in.get_center(), end=gate.get_top(), color=WHITE)
        
        self.play(Create(arrow_in))
        self.play(spike_in.animate.move_to(gate.get_top()), run_time=1)
        self.play(FadeOut(spike_in))

        # 4. Charge Accumulation (Integration)
        integration_text = Text("Charge Accumulates (Capacitance)").scale(0.5).next_to(gate, UP, buff=1)
        self.play(Write(integration_text))
        
        charge_glow = Rectangle(width=2.5, height=0.3, color=RED, fill_opacity=0.6).move_to(gate.get_center())
        self.play(FadeIn(charge_glow), run_time=1.5)
        
        threshold_text = Text("V_th Reached! Channel Inverts").scale(0.5).next_to(gate, UP, buff=1).set_color(RED)
        self.play(Transform(integration_text, threshold_text))
        
        # Invert channel
        self.play(channel.animate.set_fill(RED, opacity=0.8), run_time=0.5)

        # 5. Output Current Spike (Firing)
        fire_text = Text("I_on Spike (Action Potential)").scale(0.5).next_to(drain, RIGHT, buff=0.5)
        current_spike = Arrow(start=source.get_center(), end=drain.get_center() + RIGHT * 3, color=YELLOW, stroke_width=10, max_tip_length_to_length_ratio=0.1)
        
        self.play(Write(fire_text))
        self.play(
            GrowArrow(current_spike),
            run_time=0.5, rate_func=rush_into
        )
        
        # Reset (Leak / Refractory)
        self.play(
            FadeOut(current_spike), 
            FadeOut(charge_glow),
            channel.animate.set_fill(BLUE, opacity=0.3),
            FadeOut(integration_text),
            FadeOut(fire_text)
        )
        
        self.wait(2)
