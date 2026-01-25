"use client";

import { useState, useRef } from "react";
import { CopilotChat } from "@copilotkit/react-ui";
import { useDefaultTool, useCopilotReadable, useHumanInTheLoop } from "@copilotkit/react-core";
import { authClient } from "@/lib/auth/client";

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
          <div className="my-2 rounded-lg border-2 border-blue-200 bg-blue-50 p-4">
            <div className="font-semibold text-blue-900 mb-2">Confirm Role Preference</div>
            <p className="text-sm text-blue-800 mb-3">
              Save <strong>{(args.role as string)?.toUpperCase()}</strong> as your target role?
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => respond({ confirmed: true })}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                Confirm
              </button>
              <button
                onClick={() => respond({ confirmed: false })}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
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
          <div className="my-2 rounded-lg border-2 border-purple-200 bg-purple-50 p-4">
            <div className="font-semibold text-purple-900 mb-2">Confirm Engagement Type</div>
            <p className="text-sm text-purple-800 mb-3">
              Save <strong>{args.trinity as string}</strong> as your preferred engagement type?
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => respond({ confirmed: true })}
                className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700"
              >
                Confirm
              </button>
              <button
                onClick={() => respond({ confirmed: false })}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
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
          <div className="my-2 rounded-lg border-2 border-green-200 bg-green-50 p-4">
            <div className="font-semibold text-green-900 mb-2">Confirm Experience</div>
            <p className="text-sm text-green-800 mb-1">
              Years: <strong>{args.years as number}</strong>
            </p>
            <p className="text-sm text-green-800 mb-3">
              Industries: <strong>{industries?.join(", ")}</strong>
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => respond({ confirmed: true })}
                className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
              >
                Confirm
              </button>
              <button
                onClick={() => respond({ confirmed: false })}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
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
          <div className="my-2 rounded-lg border-2 border-orange-200 bg-orange-50 p-4">
            <div className="font-semibold text-orange-900 mb-2">Confirm Location</div>
            <p className="text-sm text-orange-800 mb-1">
              Location: <strong>{args.location as string}</strong>
            </p>
            <p className="text-sm text-orange-800 mb-3">
              Remote: <strong>{args.remote_preference as string}</strong>
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => respond({ confirmed: true })}
                className="px-3 py-1 bg-orange-600 text-white rounded text-sm hover:bg-orange-700"
              >
                Confirm
              </button>
              <button
                onClick={() => respond({ confirmed: false })}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
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
          <div className="my-2 rounded-lg border-2 border-teal-200 bg-teal-50 p-4">
            <div className="font-semibold text-teal-900 mb-2">Confirm Search Preferences</div>
            <p className="text-sm text-teal-800 mb-1">
              Day Rate: <strong>${args.day_rate_min as number} - ${args.day_rate_max as number}</strong>
            </p>
            <p className="text-sm text-teal-800 mb-3">
              Availability: <strong>{args.availability as string}</strong>
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => respond({ confirmed: true })}
                className="px-3 py-1 bg-teal-600 text-white rounded text-sm hover:bg-teal-700"
              >
                Confirm
              </button>
              <button
                onClick={() => respond({ confirmed: false })}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
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
          <div className="my-2 rounded-lg border-2 border-indigo-200 bg-indigo-50 p-4">
            <div className="font-semibold text-indigo-900 mb-2">Complete Onboarding</div>
            <p className="text-sm text-indigo-800 mb-3">
              Ready to finalize your profile and start searching for opportunities?
            </p>
            <div className="flex gap-2">
              <button
                onClick={() => respond({ confirmed: true })}
                className="px-3 py-1 bg-indigo-600 text-white rounded text-sm hover:bg-indigo-700"
              >
                Complete Setup
              </button>
              <button
                onClick={() => respond({ confirmed: false })}
                className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm hover:bg-gray-300"
              >
                Go Back
              </button>
            </div>
          </div>
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

  const steps = [
    { key: "role_preference", label: "Role", value: onboarding.role_preference },
    { key: "trinity", label: "Type", value: onboarding.trinity },
    { key: "experience", label: "Experience", value: onboarding.experience_years ? `${onboarding.experience_years}y` : undefined },
    { key: "location", label: "Location", value: onboarding.location },
    { key: "search_prefs", label: "Prefs", value: onboarding.day_rate_min ? `${onboarding.day_rate_min}-${onboarding.day_rate_max}` : undefined },
  ];

  return (
    <main className="flex min-h-screen">
      {/* Left: Profile Panel */}
      <div className="w-80 border-r border-slate-200 bg-slate-50 p-4">
        <h1 className="text-xl font-bold text-slate-900 mb-4">Fractional Quest</h1>

        {/* Progress Steps */}
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-slate-700 mb-2">Onboarding Progress</h2>
          <div className="space-y-2">
            {steps.map((step, i) => (
              <div
                key={step.key}
                className={`flex items-center gap-2 p-2 rounded ${
                  step.value ? "bg-green-100" : i === (onboarding.current_step || 0) ? "bg-blue-100" : "bg-white"
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    step.value ? "bg-green-500 text-white" : "bg-slate-300 text-slate-600"
                  }`}
                >
                  {step.value ? "!" : i + 1}
                </div>
                <div className="flex-1">
                  <div className="text-sm font-medium text-slate-700">{step.label}</div>
                  {step.value && (
                    <div className="text-xs text-slate-500">{step.value}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Profile Card */}
        {onboarding.completed && (
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <h2 className="text-sm font-semibold text-slate-700 mb-2">Your Profile</h2>
            <div className="space-y-1 text-sm text-slate-600">
              <div><strong>Role:</strong> {onboarding.role_preference?.toUpperCase()}</div>
              <div><strong>Type:</strong> {onboarding.trinity}</div>
              <div><strong>Experience:</strong> {onboarding.experience_years} years</div>
              <div><strong>Industries:</strong> {onboarding.industries?.join(", ")}</div>
              <div><strong>Location:</strong> {onboarding.location} ({onboarding.remote_preference})</div>
              <div><strong>Rate:</strong> {onboarding.day_rate_min}-{onboarding.day_rate_max}/day</div>
              <div><strong>Availability:</strong> {onboarding.availability}</div>
            </div>
          </div>
        )}
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
