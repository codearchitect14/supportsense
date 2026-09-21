import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { VoicePage } from "./VoicePage";
import { useVoiceSocket } from "../../components/voice/useVoiceSocket";

vi.mock("../../components/voice/useVoiceSocket", () => ({
  useVoiceSocket: vi.fn(),
}));

const mockedUseVoiceSocket = vi.mocked(useVoiceSocket);

function baseHookState(overrides: Partial<ReturnType<typeof useVoiceSocket>> = {}) {
  return {
    messages: [],
    conversationId: undefined,
    recordingState: "idle" as const,
    liveTranscript: "",
    audioUrl: null,
    error: null,
    startRecording: vi.fn(),
    stopRecording: vi.fn(),
    sendFeedback: vi.fn(),
    ...overrides,
  };
}

function renderVoicePage() {
  return render(
    <MemoryRouter>
      <VoicePage />
    </MemoryRouter>,
  );
}

describe("VoicePage", () => {
  beforeEach(() => {
    mockedUseVoiceSocket.mockReset();
  });

  it("shows the empty state and a mic button that starts recording when idle", () => {
    const startRecording = vi.fn();
    mockedUseVoiceSocket.mockReturnValue(baseHookState({ startRecording }));

    renderVoicePage();

    expect(screen.getByText(/press the microphone/i)).toBeInTheDocument();
    const button = screen.getByLabelText("Start recording");
    fireEvent.click(button);
    expect(startRecording).toHaveBeenCalledTimes(1);
  });

  it("switches to a stop button while recording", () => {
    const stopRecording = vi.fn();
    mockedUseVoiceSocket.mockReturnValue(
      baseHookState({ recordingState: "recording", stopRecording }),
    );

    renderVoicePage();

    const button = screen.getByLabelText("Stop recording");
    fireEvent.click(button);
    expect(stopRecording).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/listening/i)).toBeInTheDocument();
  });

  it("disables the button while processing", () => {
    mockedUseVoiceSocket.mockReturnValue(baseHookState({ recordingState: "processing" }));

    renderVoicePage();

    expect(screen.getByLabelText("Start recording")).toBeDisabled();
    expect(screen.getByText(/thinking/i)).toBeInTheDocument();
  });

  it("renders a live transcript when present", () => {
    mockedUseVoiceSocket.mockReturnValue(baseHookState({ liveTranscript: "how do refunds work" }));

    renderVoicePage();

    expect(screen.getByText("how do refunds work")).toBeInTheDocument();
  });

  it("shows an error banner when the hook reports an error", () => {
    mockedUseVoiceSocket.mockReturnValue(baseHookState({ error: "Microphone access denied" }));

    renderVoicePage();

    expect(screen.getByText("Microphone access denied")).toBeInTheDocument();
  });

  it("renders synthesized audio playback when an audio URL is available", () => {
    mockedUseVoiceSocket.mockReturnValue(baseHookState({ audioUrl: "blob:fake-audio" }));

    const { container } = renderVoicePage();

    const audio = container.querySelector("audio");
    expect(audio).toHaveAttribute("src", "blob:fake-audio");
  });
});
