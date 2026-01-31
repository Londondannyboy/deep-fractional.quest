'use client';

import { useState, useEffect, useCallback } from 'react';

interface Profile {
  role_preference?: string;
  trinity?: string;
  experience_years?: number;
  industries?: string[];
  location?: string;
  remote_preference?: string;
  day_rate_min?: number;
  day_rate_max?: number;
  availability?: string;
  onboarding_completed?: boolean;
}

interface ProfileSidebarProps {
  onboarding?: Profile;  // From agent state (may be stale)
  userName?: string | null;
  userId?: string | null;
  onProfileUpdate?: (profile: Profile) => void;
}

// Valid options for dropdowns
const ROLE_OPTIONS = ['cto', 'cfo', 'cmo', 'coo', 'cpo', 'other'];
const TRINITY_OPTIONS = ['fractional', 'interim', 'advisory', 'open'];
const REMOTE_OPTIONS = ['remote', 'hybrid', 'onsite', 'flexible'];
const AVAILABILITY_OPTIONS = ['immediately', '1_month', '3_months', 'flexible'];

export function ProfileSidebar({ onboarding, userName, userId, onProfileUpdate }: ProfileSidebarProps) {
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string>('');

  // Fetch profile from API
  const fetchProfile = useCallback(async () => {
    if (!userId) return;

    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/profile?userId=${userId}`);
      const data = await res.json();

      if (data.profile) {
        setProfile(data.profile);
        onProfileUpdate?.(data.profile);
      } else {
        setProfile(null);
      }
    } catch (err) {
      setError('Failed to fetch profile');
      console.error('[ProfileSidebar] Fetch error:', err);
    } finally {
      setLoading(false);
    }
  }, [userId, onProfileUpdate]);

  // Fetch on mount and when userId changes
  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  // Also update when onboarding state changes (from agent)
  useEffect(() => {
    if (onboarding && Object.keys(onboarding).length > 0) {
      setProfile(prev => ({ ...prev, ...onboarding }));
    }
  }, [onboarding]);

  // Save a field to the API
  const saveField = async (field: string, value: any) => {
    if (!userId) {
      setError('Sign in to save your profile');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const res = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ user_id: userId, [field]: value }),
      });

      const data = await res.json();
      if (data.success) {
        setProfile(data.profile);
        onProfileUpdate?.(data.profile);
        setEditingField(null);
      } else {
        setError(data.error || 'Failed to save');
      }
    } catch (err) {
      setError('Failed to save');
      console.error('[ProfileSidebar] Save error:', err);
    } finally {
      setSaving(false);
    }
  };

  // Start editing a field
  const startEdit = (field: string, currentValue: any) => {
    setEditingField(field);
    setEditValue(currentValue?.toString() || '');
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingField(null);
    setEditValue('');
  };

  // Get display value
  const getDisplayValue = (field: string): string => {
    if (!profile) return '—';

    switch (field) {
      case 'role_preference':
        return profile.role_preference?.toUpperCase() || '—';
      case 'trinity':
        return profile.trinity || '—';
      case 'experience_years':
        return profile.experience_years !== undefined
          ? `${profile.experience_years} years`
          : '—';
      case 'industries':
        return profile.industries?.join(', ') || '—';
      case 'location':
        return profile.location || '—';
      case 'remote_preference':
        return profile.remote_preference || '—';
      case 'day_rate_min':
        return profile.day_rate_min !== undefined
          ? `£${profile.day_rate_min}`
          : '—';
      case 'day_rate_max':
        return profile.day_rate_max !== undefined
          ? `£${profile.day_rate_max}`
          : '—';
      case 'availability':
        return profile.availability || '—';
      default:
        return '—';
    }
  };

  // Render edit control for a field
  const renderEditControl = (field: string) => {
    if (field === 'role_preference') {
      return (
        <select
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className="w-full p-1 text-xs border rounded"
          autoFocus
        >
          <option value="">Select role...</option>
          {ROLE_OPTIONS.map(opt => (
            <option key={opt} value={opt}>{opt.toUpperCase()}</option>
          ))}
        </select>
      );
    }
    if (field === 'trinity') {
      return (
        <select
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className="w-full p-1 text-xs border rounded"
          autoFocus
        >
          <option value="">Select type...</option>
          {TRINITY_OPTIONS.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );
    }
    if (field === 'remote_preference') {
      return (
        <select
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className="w-full p-1 text-xs border rounded"
          autoFocus
        >
          <option value="">Select preference...</option>
          {REMOTE_OPTIONS.map(opt => (
            <option key={opt} value={opt}>{opt}</option>
          ))}
        </select>
      );
    }
    if (field === 'availability') {
      return (
        <select
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className="w-full p-1 text-xs border rounded"
          autoFocus
        >
          <option value="">Select availability...</option>
          {AVAILABILITY_OPTIONS.map(opt => (
            <option key={opt} value={opt}>{opt.replace('_', ' ')}</option>
          ))}
        </select>
      );
    }
    if (field === 'experience_years' || field === 'day_rate_min' || field === 'day_rate_max') {
      return (
        <input
          type="number"
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          className="w-full p-1 text-xs border rounded"
          autoFocus
        />
      );
    }
    // Default text input
    return (
      <input
        type="text"
        value={editValue}
        onChange={(e) => setEditValue(e.target.value)}
        className="w-full p-1 text-xs border rounded"
        autoFocus
      />
    );
  };

  // Profile fields configuration
  const fields = [
    { key: 'role_preference', label: 'Target Role', icon: '🎯' },
    { key: 'trinity', label: 'Engagement', icon: '📋' },
    { key: 'experience_years', label: 'Experience', icon: '⭐' },
    { key: 'industries', label: 'Industries', icon: '🏢' },
    { key: 'location', label: 'Location', icon: '📍' },
    { key: 'remote_preference', label: 'Remote Pref', icon: '🏠' },
    { key: 'day_rate_min', label: 'Min Rate', icon: '💷' },
    { key: 'day_rate_max', label: 'Max Rate', icon: '💰' },
    { key: 'availability', label: 'Availability', icon: '📅' },
  ];

  const completedFields = fields.filter(f => {
    const val = profile?.[f.key as keyof Profile];
    return val !== undefined && val !== null && val !== '';
  }).length;

  const progressPercent = (completedFields / fields.length) * 100;

  return (
    <div className="bg-white rounded-xl shadow-lg border border-indigo-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-500 px-4 py-3">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-white text-sm flex items-center gap-2">
            <span>✨</span> {userName ? `${userName}'s Profile` : 'Your Profile'}
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchProfile}
              className="text-white/70 hover:text-white text-xs"
              title="Refresh"
            >
              🔄
            </button>
            <span className="text-xs bg-white/20 text-white px-2 py-1 rounded-full">
              {completedFields}/{fields.length}
            </span>
          </div>
        </div>
        {/* Progress bar */}
        <div className="mt-2 h-1.5 bg-white/20 rounded-full overflow-hidden">
          <div
            className="h-full bg-white transition-all duration-500 ease-out"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Loading/Error state */}
      {loading && (
        <div className="p-4 text-center text-gray-500 text-sm">Loading...</div>
      )}
      {error && (
        <div className="p-2 bg-red-50 text-red-600 text-xs">{error}</div>
      )}

      {/* Profile fields */}
      <div className="p-3 space-y-2 max-h-80 overflow-y-auto">
        {fields.map((field) => {
          const isEditing = editingField === field.key;
          const value = getDisplayValue(field.key);
          const hasValue = value !== '—';

          return (
            <div
              key={field.key}
              className={`
                flex items-center gap-2 p-2 rounded-lg transition-all text-xs
                ${hasValue ? 'bg-indigo-50 border border-indigo-100' : 'bg-gray-50 border border-gray-100'}
              `}
            >
              <span className="text-sm">{field.icon}</span>

              <div className="flex-1 min-w-0">
                <p className="text-xs text-gray-500 font-medium">{field.label}</p>

                {isEditing ? (
                  <div className="flex gap-1 mt-1">
                    {renderEditControl(field.key)}
                    <button
                      onClick={() => {
                        let val: any = editValue;
                        if (field.key === 'experience_years' || field.key === 'day_rate_min' || field.key === 'day_rate_max') {
                          val = parseInt(editValue, 10) || 0;
                        }
                        if (field.key === 'industries') {
                          val = editValue.split(',').map(s => s.trim()).filter(Boolean);
                        }
                        saveField(field.key, val);
                      }}
                      disabled={saving}
                      className="px-2 py-1 bg-indigo-500 text-white rounded text-xs hover:bg-indigo-600 disabled:opacity-50"
                    >
                      {saving ? '...' : '✓'}
                    </button>
                    <button
                      onClick={cancelEdit}
                      className="px-2 py-1 bg-gray-200 rounded text-xs hover:bg-gray-300"
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <p className={`truncate ${hasValue ? 'text-gray-800' : 'text-gray-400 italic'}`}>
                    {value}
                  </p>
                )}
              </div>

              {!isEditing && userId && (
                <button
                  onClick={() => startEdit(field.key, profile?.[field.key as keyof Profile])}
                  className="text-gray-400 hover:text-indigo-500 text-xs"
                  title="Edit"
                >
                  ✏️
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-100">
        {profile?.onboarding_completed ? (
          <p className="text-sm text-indigo-600 font-medium">🎉 Profile complete!</p>
        ) : (
          <p className="text-xs text-gray-500">
            {userId ? 'Click ✏️ to edit any field' : 'Sign in to save your profile'}
          </p>
        )}
        {userId && (
          <p className="text-xs text-gray-400 mt-1 truncate">ID: {userId.slice(0, 8)}...</p>
        )}
      </div>
    </div>
  );
}

export default ProfileSidebar;
