'use client';

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

interface ProfileSidebarProps {
  onboarding: OnboardingState;
  userName?: string | null;
  userId?: string | null;
}

// Profile fields in order
const PROFILE_FIELDS = [
  { key: 'role_preference', label: 'Target Role', icon: '🎯', step: 1 },
  { key: 'trinity', label: 'Engagement Type', icon: '📋', step: 2 },
  { key: 'experience', label: 'Experience', icon: '⭐', step: 3 },
  { key: 'location', label: 'Location', icon: '📍', step: 4 },
  { key: 'search_prefs', label: 'Day Rate', icon: '💰', step: 5 },
];

export function ProfileSidebar({ onboarding, userName, userId }: ProfileSidebarProps) {
  const isComplete = onboarding.completed;
  const currentStep = onboarding.current_step || 0;

  // Calculate completion
  const completedSteps = [
    onboarding.role_preference,
    onboarding.trinity,
    onboarding.experience_years !== undefined,
    onboarding.location,
    onboarding.day_rate_min !== undefined,
  ].filter(Boolean).length;

  const progressPercent = (completedSteps / 5) * 100;

  // Get display value for a field
  const getValue = (key: string): string | null => {
    switch (key) {
      case 'role_preference':
        return onboarding.role_preference?.toUpperCase() || null;
      case 'trinity':
        return onboarding.trinity || null;
      case 'experience':
        if (onboarding.experience_years === undefined) return null;
        const industries = onboarding.industries?.join(', ') || '';
        return `${onboarding.experience_years}yr${industries ? ` • ${industries}` : ''}`;
      case 'location':
        if (!onboarding.location) return null;
        return `${onboarding.location}${onboarding.remote_preference ? ` (${onboarding.remote_preference})` : ''}`;
      case 'search_prefs':
        if (onboarding.day_rate_min === undefined) return null;
        return `$${onboarding.day_rate_min}-$${onboarding.day_rate_max}${onboarding.availability ? ` • ${onboarding.availability}` : ''}`;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg border border-indigo-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-500 px-4 py-3">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-white text-sm flex items-center gap-2">
            <span>✨</span> {userName ? `${userName}'s Profile` : 'Your Profile'}
          </h3>
          {isComplete ? (
            <span className="text-xs bg-white/20 text-white px-2 py-1 rounded-full">
              ✓ Complete
            </span>
          ) : (
            <span className="text-xs bg-white/20 text-white px-2 py-1 rounded-full">
              {completedSteps}/5
            </span>
          )}
        </div>
        {/* Progress bar */}
        <div className="mt-2 h-1.5 bg-white/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-white transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Profile items */}
      <div className="p-4 space-y-3">
        {PROFILE_FIELDS.map((field) => {
          const value = getValue(field.key);
          const isSet = value !== null;
          const isCurrent = field.step === currentStep + 1;

          return (
            <div
              key={field.key}
              className={`
                flex items-start gap-3 p-3 rounded-lg transition-all
                ${isSet
                  ? 'bg-indigo-50 border border-indigo-100'
                  : isCurrent
                    ? 'bg-amber-50 border border-amber-200'
                    : 'bg-gray-50 border border-gray-100'
                }
              `}
            >
              {/* Status indicator */}
              <div className={`
                w-7 h-7 rounded-full flex items-center justify-center text-sm flex-shrink-0
                ${isSet
                  ? 'bg-indigo-500 text-white'
                  : isCurrent
                    ? 'bg-amber-400 text-white'
                    : 'bg-gray-200 text-gray-400'
                }
              `}>
                {isSet ? '✓' : field.icon}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className={`text-xs font-semibold uppercase tracking-wide mb-0.5 ${
                  isSet ? 'text-indigo-600' : isCurrent ? 'text-amber-600' : 'text-gray-400'
                }`}>
                  {field.label}
                </p>
                {value ? (
                  <p className="text-sm text-gray-800 truncate">{value}</p>
                ) : isCurrent ? (
                  <p className="text-xs text-amber-500 italic">Answering now...</p>
                ) : (
                  <p className="text-xs text-gray-400">Not set</p>
                )}
              </div>

              {/* Confirmed badge */}
              {isSet && (
                <span className="text-xs text-indigo-400 flex-shrink-0">
                  DB ✓
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
        {isComplete ? (
          <p className="text-sm text-indigo-600 font-medium">
            🎉 Ready to search for jobs!
          </p>
        ) : (
          <p className="text-xs text-gray-500">
            {5 - completedSteps} more step{5 - completedSteps !== 1 ? 's' : ''} to complete
          </p>
        )}
        {userId && (
          <p className="text-xs text-gray-400 mt-1 truncate">
            ID: {userId.slice(0, 8)}...
          </p>
        )}
      </div>
    </div>
  );
}

export default ProfileSidebar;
