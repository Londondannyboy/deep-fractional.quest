"use client";

import { useState, useRef } from "react";
import { CopilotChat } from "@copilotkit/react-ui";
import { useDefaultTool, useCopilotReadable } from "@copilotkit/react-core";

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

  // Make onboarding state readable to agent
  useCopilotReadable({
    description: "Current onboarding progress and user profile",
    value: onboarding,
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
