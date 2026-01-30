"use client";

import { useState, useRef, useCallback } from "react";
import { CopilotChat } from "@copilotkit/react-ui";
import { useDefaultTool, useCopilotReadable, useHumanInTheLoop, useCopilotChat } from "@copilotkit/react-core";
import { TextMessage, Role } from "@copilotkit/runtime-client-gql";
import { authClient } from "@/lib/auth/client";
import { VoiceInput } from "@/components/VoiceInput";
import { HITLCard } from "@/components/HITLCard";
import { ProfileSidebar } from "@/components/ProfileSidebar";

// Types matching backend state
interface OnboardingState {
  current_step?: number;
  completed?: boolean;
  role_preference?: string;
  trinity?: string;
  experience_years?: number;
  industries?: string[];
  location?: string;
  remote_preference?: string;
  day_rate_min?: number;
  day_rate_max?: number;
  availability?: string;
}

export default function Home() {
  const [onboarding, setOnboarding] = useState<OnboardingState>({
    current_step: 0,
    completed: false,
  });
  const processedKeyRef = useRef<string | null>(null);

  // Get authenticated user session
  const { data: session } = authClient.useSession();
  const userId = session?.user?.id;
  const firstName = session?.user?.name?.split(" ")[0];

  // CopilotKit chat for voice integration
  const { appendMessage } = useCopilotChat();

  // Handle voice messages - forward to CopilotKit chat
  const handleVoiceMessage = useCallback(
    (text: string, role: "user" | "assistant") => {
      const message = new TextMessage({
        content: text,
        role: role === "user" ? Role.User : Role.Assistant,
      });
      appendMessage(message);
    },
    [appendMessage]
  );

  // Capture tool results and update state
  useDefaultTool({
    render: ({ name, status, args, result }) => {
      // Update onboarding state when tools complete
      if (status === "complete" && result?.success) {
        const key = JSON.stringify({ name, result });

        if (processedKeyRef.current !== key) {
          processedKeyRef.current = key;

          queueMicrotask(() => {
            setOnboarding((prev) => ({
              ...prev,
              ...(result.role_preference && { role_preference: result.role_preference }),
              ...(result.trinity && { trinity: result.trinity }),
              ...(result.experience_years !== undefined && { experience_years: result.experience_years }),
              ...(result.industries && { industries: result.industries }),
              ...(result.location && { location: result.location }),
              ...(result.remote_preference && { remote_preference: result.remote_preference }),
              ...(result.day_rate_min !== undefined && { day_rate_min: result.day_rate_min }),
              ...(result.day_rate_max !== undefined && { day_rate_max: result.day_rate_max }),
              ...(result.availability && { availability: result.availability }),
              ...(result.current_step !== undefined && { current_step: result.current_step }),
              ...(result.completed !== undefined && { completed: result.completed }),
            }));
          });
        }
      }

      // Render tool call UI
      return (
        <details className="my-2 rounded border border-slate-200 bg-white p-2 text-xs">
          <summary className="cursor-pointer text-slate-700">
            {status === "complete" ? `Called ${name}` : `Calling ${name}...`}
          </summary>
          <div className="mt-2 space-y-1 text-slate-600">
            <div>Status: {status}</div>
            <div>Args: <pre className="whitespace-pre-wrap">{JSON.stringify(args, null, 2)}</pre></div>
            {result && <div>Result: <pre className="whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre></div>}
          </div>
        </details>
      );
    },
  });

  // Make onboarding state and user ID readable to agent
  useCopilotReadable({
    description: "Current onboarding progress, user profile, and authenticated user ID",
    value: {
      ...onboarding,
      user_id: userId,  // Pass authenticated user ID to agent for persistence
    },
  });

  // HITL: Confirm role preference before saving
  useHumanInTheLoop({
    name: "confirm_role_preference",
    description: "Confirm the C-level role preference before saving",
    parameters: [
      { name: "role", type: "string", description: "The C-level role", required: true },
    ],
    render: ({ args, status, respond }) => {
      if (status === "executing" && respond) {
        return (
          <HITLCard
            title="Confirm Role Preference"
            description={`Save ${(args.role as string)?.toUpperCase()} as your target C-level role?`}
            confirmLabel="Yes, save this"
            cancelLabel="Not now"
            onConfirm={() => respond({ confirmed: true })}
            onCancel={() => respond({ confirmed: false })}
            countdownSeconds={15}
            autoAction="cancel"
            colorScheme="blue"
          />
        );
      }
      if (status === "complete") {
        return <div className="text-xs text-gray-500 my-1">Role preference saved</div>;
      }
      return <></>;
    },
  });

  // HITL: Confirm engagement type (trinity)
  useHumanInTheLoop({
    name: "confirm_trinity",
    description: "Confirm the engagement type before saving",
    parameters: [
      { name: "trinity", type: "string", description: "Engagement type", required: true },
    ],
    render: ({ args, status, respond }) => {
      if (status === "executing" && respond) {
        return (
          <HITLCard
            title="Confirm Engagement Type"
            description={`Save ${args.trinity as string} as your preferred engagement type (Fractional/Interim/Advisory)?`}
            onConfirm={() => respond({ confirmed: true })}
            onCancel={() => respond({ confirmed: false })}
            countdownSeconds={15}
            autoAction="cancel"
            colorScheme="purple"
          />
        );
      }
      if (status === "complete") {
        return <div className="text-xs text-gray-500 my-1">Engagement type saved</div>;
      }
      return <></>;
    },
  });

  // HITL: Confirm experience
  useHumanInTheLoop({
    name: "confirm_experience",
    description: "Confirm experience details before saving",
    parameters: [
      { name: "years", type: "number", description: "Years of experience", required: true },
      { name: "industries", type: "string[]", description: "Industries", required: true },
    ],
    render: ({ args, status, respond }) => {
      if (status === "executing" && respond) {
        const industries = args.industries as string[];
        return (
          <HITLCard
            title="Confirm Experience"
            description={`Save ${args.years as number} years experience in ${industries?.join(", ")}?`}
            onConfirm={() => respond({ confirmed: true })}
            onCancel={() => respond({ confirmed: false })}
            countdownSeconds={15}
            autoAction="cancel"
            colorScheme="green"
          />
        );
      }
      if (status === "complete") {
        return <div className="text-xs text-gray-500 my-1">Experience saved</div>;
      }
      return <></>;
    },
  });

  // HITL: Confirm location
  useHumanInTheLoop({
    name: "confirm_location",
    description: "Confirm location preferences before saving",
    parameters: [
      { name: "location", type: "string", description: "Location", required: true },
      { name: "remote_preference", type: "string", description: "Remote preference", required: true },
    ],
    render: ({ args, status, respond }) => {
      if (status === "executing" && respond) {
        return (
          <HITLCard
            title="Confirm Location"
            description={`Save ${args.location as string} (${args.remote_preference as string}) as your location preference?`}
            onConfirm={() => respond({ confirmed: true })}
            onCancel={() => respond({ confirmed: false })}
            countdownSeconds={15}
            autoAction="cancel"
            colorScheme="orange"
          />
        );
      }
      if (status === "complete") {
        return <div className="text-xs text-gray-500 my-1">Location saved</div>;
      }
      return <></>;
    },
  });

  // HITL: Confirm search preferences
  useHumanInTheLoop({
    name: "confirm_search_prefs",
    description: "Confirm compensation and availability before saving",
    parameters: [
      { name: "day_rate_min", type: "number", description: "Minimum day rate", required: true },
      { name: "day_rate_max", type: "number", description: "Maximum day rate", required: true },
      { name: "availability", type: "string", description: "Availability", required: true },
    ],
    render: ({ args, status, respond }) => {
      if (status === "executing" && respond) {
        return (
          <HITLCard
            title="Confirm Search Preferences"
            description={`Save day rate $${args.day_rate_min}-$${args.day_rate_max} with ${args.availability as string} availability?`}
            onConfirm={() => respond({ confirmed: true })}
            onCancel={() => respond({ confirmed: false })}
            countdownSeconds={15}
            autoAction="cancel"
            colorScheme="teal"
          />
        );
      }
      if (status === "complete") {
        return <div className="text-xs text-gray-500 my-1">Search preferences saved</div>;
      }
      return <></>;
    },
  });

  // HITL: Confirm complete onboarding
  useHumanInTheLoop({
    name: "complete_onboarding",
    description: "Confirm to finalize onboarding",
    parameters: [],
    render: ({ status, respond }) => {
      if (status === "executing" && respond) {
        return (
          <HITLCard
            title="Complete Onboarding"
            description="Ready to finalize your profile and start searching for opportunities?"
            confirmLabel="Complete Setup"
            cancelLabel="Go Back"
            onConfirm={() => respond({ confirmed: true })}
            onCancel={() => respond({ confirmed: false })}
            countdownSeconds={20}
            autoAction="cancel"
            colorScheme="blue"
          />
        );
      }
      if (status === "complete") {
        return (
          <div className="my-2 rounded-lg bg-green-100 p-3 text-green-800 text-sm">
            Onboarding complete! You can now search for jobs and coaching.
          </div>
        );
      }
      return <></>;
    },
  });

  // HITL: Confirm saving a job
  useHumanInTheLoop({
    name: "save_job",
    description: "Confirm saving a job to your list",
    parameters: [
      { name: "job_id", type: "string", description: "Job ID", required: true },
      { name: "notes", type: "string", description: "Notes", required: false },
    ],
    render: ({ args, status, respond }) => {
      if (status === "executing" && respond) {
        return (
          <HITLCard
            title="Save Job"
            description={`Save this job to your list?${args.notes ? ` Notes: ${args.notes}` : ""}`}
            confirmLabel="Save Job"
            cancelLabel="Cancel"
            onConfirm={() => respond({ confirmed: true })}
            onCancel={() => respond({ confirmed: false })}
            countdownSeconds={15}
            autoAction="cancel"
            colorScheme="green"
          />
        );
      }
      if (status === "complete") {
        return <div className="text-xs text-gray-500 my-1">Job saved to your list</div>;
      }
      return <></>;
    },
  });

  // HITL: Confirm updating job status
  useHumanInTheLoop({
    name: "update_job_status",
    description: "Confirm updating job application status",
    parameters: [
      { name: "job_id", type: "string", description: "Job ID", required: true },
      { name: "status", type: "string", description: "New status", required: true },
      { name: "notes", type: "string", description: "Notes", required: false },
    ],
    render: ({ args, status, respond }) => {
      if (status === "executing" && respond) {
        return (
          <HITLCard
            title="Update Job Status"
            description={`Update status to ${args.status}?${args.notes ? ` Notes: ${args.notes}` : ""}`}
            confirmLabel="Update Status"
            cancelLabel="Cancel"
            onConfirm={() => respond({ confirmed: true })}
            onCancel={() => respond({ confirmed: false })}
            countdownSeconds={15}
            autoAction="cancel"
            colorScheme="orange"
          />
        );
      }
      if (status === "complete") {
        return <div className="text-xs text-gray-500 my-1">Job status updated</div>;
      }
      return <></>;
    },
  });

  // HITL: Schedule coaching session
  useHumanInTheLoop({
    name: "schedule_session",
    description: "Confirm scheduling a coaching session",
    parameters: [
      { name: "coach_id", type: "string", description: "Coach ID", required: true },
      { name: "session_type", type: "string", description: "Session type", required: true },
      { name: "preferred_date", type: "string", description: "Preferred date", required: false },
      { name: "topic", type: "string", description: "Topic to discuss", required: false },
    ],
    render: ({ args, status, respond }) => {
      if (status === "executing" && respond) {
        const sessionLabels: Record<string, string> = {
          intro_call: "Free 15-min Intro Call",
          coaching_session: "60-min Coaching Session",
          strategy_deep_dive: "90-min Strategy Deep Dive",
        };
        const sessionLabel = sessionLabels[args.session_type as string] || args.session_type;
        const details = [
          `Session: ${sessionLabel}`,
          args.preferred_date && `Date: ${args.preferred_date}`,
          args.topic && `Topic: ${args.topic}`,
        ].filter(Boolean).join(" | ");

        return (
          <HITLCard
            title="Schedule Coaching Session"
            description={details}
            confirmLabel="Book Session"
            cancelLabel="Cancel"
            onConfirm={() => respond({ confirmed: true })}
            onCancel={() => respond({ confirmed: false })}
            countdownSeconds={20}
            autoAction="cancel"
            colorScheme="purple"
          />
        );
      }
      if (status === "complete") {
        return <div className="text-xs text-gray-500 my-1">Session request submitted</div>;
      }
      return <></>;
    },
  });

  // HITL: Cancel coaching session
  useHumanInTheLoop({
    name: "cancel_session",
    description: "Confirm cancelling a coaching session",
    parameters: [
      { name: "session_id", type: "string", description: "Session ID", required: true },
      { name: "reason", type: "string", description: "Cancellation reason", required: false },
    ],
    render: ({ args, status, respond }) => {
      if (status === "executing" && respond) {
        return (
          <HITLCard
            title="Cancel Coaching Session"
            description={`Are you sure you want to cancel this session?${args.reason ? ` Reason: ${args.reason as string}` : ""}`}
            confirmLabel="Cancel Session"
            cancelLabel="Keep Session"
            onConfirm={() => respond({ confirmed: true })}
            onCancel={() => respond({ confirmed: false })}
            countdownSeconds={15}
            autoAction="cancel"
            colorScheme="red"
          />
        );
      }
      if (status === "complete") {
        return <div className="text-xs text-gray-500 my-1">Session cancelled</div>;
      }
      return <></>;
    },
  });

  return (
    <main className="flex min-h-screen">
      {/* Left: Profile Panel */}
      <div className="w-80 border-r border-slate-200 bg-slate-50 p-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-slate-900">Fractional Quest</h1>
        </div>

        {/* Auth Status */}
        <div className="mb-4 p-3 rounded-lg bg-white border border-slate-200">
          {session?.user ? (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-sm font-bold">
                {firstName?.[0]?.toUpperCase() || "U"}
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-slate-900">{session.user.name || session.user.email}</div>
                <div className="text-xs text-slate-500">Signed in</div>
              </div>
              <a href="/auth/sign-out" className="text-xs text-slate-400 hover:text-slate-600">Sign out</a>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-600">Not signed in</span>
              <a href="/auth/sign-in" className="text-sm font-medium text-indigo-600 hover:text-indigo-800">Sign in</a>
            </div>
          )}
        </div>

        {/* Voice Chat Button */}
        <div className="mb-6">
          <VoiceInput
            onMessage={handleVoiceMessage}
            firstName={firstName}
            userId={userId}
            pageContext={{ pageType: onboarding.completed ? "jobs" : "home" }}
          />
        </div>

        {/* Profile Sidebar - shows confirmed data from database */}
        <ProfileSidebar
          onboarding={onboarding}
          userName={firstName}
          userId={userId}
        />
      </div>

      {/* Right: Chat Panel */}
      <div className="flex-1 flex flex-col">
        <CopilotChat
          className="flex-1"
          labels={{
            title: "Career Assistant",
            initial: "Hi! I'm here to help you find fractional executive opportunities. What type of C-level role are you looking for?",
          }}
        />
      </div>
    </main>
  );
}
