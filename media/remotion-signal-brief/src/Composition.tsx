import React from "react";
import { AbsoluteFill, Composition, Easing, interpolate, Sequence, useCurrentFrame } from "remotion";

export type SignalBriefProps = {
  source: string;
  headline: string;
  hook: string;
  context: string;
  instruction: string;
  review: string;
  cta: string;
  accent: string;
};

const sceneFrames = 180;

const Enter: React.FC<{ children: React.ReactNode; delay?: number }> = ({ children, delay = 0 }) => {
  const frame = useCurrentFrame();
  return <div style={{ opacity: interpolate(frame - delay, [0, 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) }), translate: `0 ${interpolate(frame - delay, [0, 20], [34, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.bezier(0.16, 1, 0.3, 1) })}px` }}>{children}</div>;
};

const Frame: React.FC<{ eyebrow: string; message: string; detail?: string; accent: string; index: number }> = ({ eyebrow, message, detail, accent, index }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, sceneFrames], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ backgroundColor: "#101316", color: "#ebe7df", fontFamily: "Arial, sans-serif", padding: "120px 88px", overflow: "hidden" }}>
    <div style={{ position: "absolute", width: 760, height: 760, borderRadius: 999, background: accent, opacity: 0.09, right: -320, top: -260, scale: interpolate(frame, [0, sceneFrames], [0.86, 1.08], { extrapolateRight: "clamp" }) }} />
    <div style={{ position: "absolute", inset: 42, border: "2px solid #2b3237", borderRadius: 44 }} />
    <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", height: "100%", position: "relative" }}>
      <Enter><div style={{ color: accent, fontFamily: "monospace", fontSize: 30, letterSpacing: 6, textTransform: "uppercase" }}>{eyebrow}</div></Enter>
      <div style={{ display: "flex", flexDirection: "column", gap: 44 }}><Enter delay={8}><div style={{ fontSize: message.length > 82 ? 78 : 92, lineHeight: 1.02, letterSpacing: -4, fontWeight: 600, maxWidth: 880 }}>{message}</div></Enter>{detail && <Enter delay={16}><div style={{ color: "#929ca2", fontSize: 42, lineHeight: 1.3, maxWidth: 860 }}>{detail}</div></Enter>}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 22 }}><div style={{ width: 76, height: 76, display: "grid", placeItems: "center", borderRadius: 22, background: accent, color: "#172019", fontSize: 28, fontWeight: 700 }}>{index}</div><div style={{ height: 8, flex: 1, borderRadius: 99, background: "#293036", overflow: "hidden" }}><div style={{ width: `${progress * 100}%`, height: "100%", background: accent }} /></div><div style={{ fontFamily: "monospace", color: "#6f7980", fontSize: 26 }}>{index}/5</div></div>
    </div>
  </AbsoluteFill>;
};

export const SignalBriefVideo: React.FC<SignalBriefProps> = (props) => <AbsoluteFill>
  <Sequence durationInFrames={sceneFrames}><Frame eyebrow={props.source} message={props.hook} detail={props.headline} accent={props.accent} index={1} /></Sequence>
  <Sequence from={sceneFrames} durationInFrames={sceneFrames}><Frame eyebrow="START WITH CONTEXT" message={props.context} detail="Use the materials already behind the work." accent="#8cb3c3" index={2} /></Sequence>
  <Sequence from={sceneFrames * 2} durationInFrames={sceneFrames}><Frame eyebrow="GIVE A CLEAR JOB" message={props.instruction} detail="Ask for the first usable version—not a vague brainstorm." accent="#d2b59b" index={3} /></Sequence>
  <Sequence from={sceneFrames * 3} durationInFrames={sceneFrames}><Frame eyebrow="KEEP THE HUMAN GATE" message={props.review} detail="Evidence and judgment stay visible before the next action." accent="#a8c2ae" index={4} /></Sequence>
  <Sequence from={sceneFrames * 4} durationInFrames={sceneFrames}><Frame eyebrow="SIGNAL → WORKFLOW" message={props.cta} detail="Log the repeated steps. Automate the smallest safe boundary." accent={props.accent} index={5} /></Sequence>
</AbsoluteFill>;

export const MyComposition = () => <Composition id="SignalBrief" component={SignalBriefVideo} durationInFrames={sceneFrames * 5} fps={30} width={1080} height={1920} defaultProps={{ source: "OPENAI ACADEMY", headline: "How to use ChatGPT Work for everyday tasks", hook: "Stop starting important work from a blank prompt.", context: "Give the agent your real inputs, constraints, and destination format.", instruction: "Ask for a review-ready brief, plan, deck, workbook, or process document.", review: "Inspect the evidence. Refine the judgment. Approve what happens next.", cta: "Turn one repeated workflow into a reusable template.", accent: "#a8c2ae" }} />;
