'use client';

import { useState, useEffect, useCallback } from 'react';

interface HITLCardProps {
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  countdownSeconds?: number;
  autoAction?: 'confirm' | 'cancel' | 'none';
  colorScheme?: 'blue' | 'purple' | 'green' | 'orange' | 'teal' | 'indigo' | 'emerald' | 'amber';
  children?: React.ReactNode;
}

const colorSchemes = {
  blue: {
    border: 'border-blue-200',
    bg: 'bg-blue-50',
    title: 'text-blue-900',
    text: 'text-blue-800',
    button: 'bg-blue-600 hover:bg-blue-700',
    progress: 'bg-blue-500',
    progressBg: 'bg-blue-200',
  },
  purple: {
    border: 'border-purple-200',
    bg: 'bg-purple-50',
    title: 'text-purple-900',
    text: 'text-purple-800',
    button: 'bg-purple-600 hover:bg-purple-700',
    progress: 'bg-purple-500',
    progressBg: 'bg-purple-200',
  },
  green: {
    border: 'border-green-200',
    bg: 'bg-green-50',
    title: 'text-green-900',
    text: 'text-green-800',
    button: 'bg-green-600 hover:bg-green-700',
    progress: 'bg-green-500',
    progressBg: 'bg-green-200',
  },
  orange: {
    border: 'border-orange-200',
    bg: 'bg-orange-50',
    title: 'text-orange-900',
    text: 'text-orange-800',
    button: 'bg-orange-600 hover:bg-orange-700',
    progress: 'bg-orange-500',
    progressBg: 'bg-orange-200',
  },
  teal: {
    border: 'border-teal-200',
    bg: 'bg-teal-50',
    title: 'text-teal-900',
    text: 'text-teal-800',
    button: 'bg-teal-600 hover:bg-teal-700',
    progress: 'bg-teal-500',
    progressBg: 'bg-teal-200',
  },
  indigo: {
    border: 'border-indigo-200',
    bg: 'bg-indigo-50',
    title: 'text-indigo-900',
    text: 'text-indigo-800',
    button: 'bg-indigo-600 hover:bg-indigo-700',
    progress: 'bg-indigo-500',
    progressBg: 'bg-indigo-200',
  },
  emerald: {
    border: 'border-emerald-200',
    bg: 'bg-emerald-50',
    title: 'text-emerald-900',
    text: 'text-emerald-800',
    button: 'bg-emerald-600 hover:bg-emerald-700',
    progress: 'bg-emerald-500',
    progressBg: 'bg-emerald-200',
  },
  amber: {
    border: 'border-amber-200',
    bg: 'bg-amber-50',
    title: 'text-amber-900',
    text: 'text-amber-800',
    button: 'bg-amber-600 hover:bg-amber-700',
    progress: 'bg-amber-500',
    progressBg: 'bg-amber-200',
  },
};

export function HITLCard({
  title,
  description,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  countdownSeconds = 15,
  autoAction = 'none',
  colorScheme = 'blue',
  children,
}: HITLCardProps) {
  const [timeLeft, setTimeLeft] = useState(countdownSeconds);
  const [isPaused, setIsPaused] = useState(false);
  const colors = colorSchemes[colorScheme];

  const handleConfirm = useCallback(() => {
    setIsPaused(true);
    onConfirm();
  }, [onConfirm]);

  const handleCancel = useCallback(() => {
    setIsPaused(true);
    onCancel();
  }, [onCancel]);

  // Countdown timer
  useEffect(() => {
    if (isPaused || autoAction === 'none') return;

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          if (autoAction === 'confirm') {
            handleConfirm();
          } else if (autoAction === 'cancel') {
            handleCancel();
          }
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isPaused, autoAction, handleConfirm, handleCancel]);

  // Pause countdown on hover
  const handleMouseEnter = () => setIsPaused(true);
  const handleMouseLeave = () => setIsPaused(false);

  const progressPercent = (timeLeft / countdownSeconds) * 100;

  return (
    <div
      className={`my-2 rounded-lg border-2 ${colors.border} ${colors.bg} p-4 transition-all`}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className={`font-semibold ${colors.title} mb-2 flex items-center justify-between`}>
        <span>{title}</span>
        {autoAction !== 'none' && (
          <span className="text-xs font-normal opacity-70">
            {isPaused ? 'Paused' : `${timeLeft}s`}
          </span>
        )}
      </div>

      <p className={`text-sm ${colors.text} mb-3`}>{description}</p>

      {children}

      {/* Countdown progress bar */}
      {autoAction !== 'none' && (
        <div className={`h-1 ${colors.progressBg} rounded-full mb-3 overflow-hidden`}>
          <div
            className={`h-full ${colors.progress} transition-all duration-1000 ease-linear`}
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={handleConfirm}
          className={`px-4 py-2 ${colors.button} text-white rounded text-sm font-medium transition-colors`}
        >
          {confirmLabel}
        </button>
        <button
          onClick={handleCancel}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded text-sm font-medium hover:bg-gray-300 transition-colors"
        >
          {cancelLabel}
        </button>
      </div>

      {autoAction !== 'none' && (
        <p className="text-xs mt-2 opacity-60">
          {autoAction === 'cancel' ? 'Will auto-cancel' : 'Will auto-confirm'} if no response. Hover to pause.
        </p>
      )}
    </div>
  );
}
