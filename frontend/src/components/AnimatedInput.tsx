import type { ChangeEvent, KeyboardEvent } from 'react';
import '../styles/input.css';

interface AnimatedInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  placeholder?: string;
  /** Stretches the input to fill its row, for the bottom-of-screen chat layout. */
  wide?: boolean;
}

/** Animated glowing text input used for both the landing prompt and the chat composer. */
export function AnimatedInput({ value, onChange, onSubmit, disabled, placeholder, wide }: AnimatedInputProps) {
  const submit = () => {
    if (!disabled && value.trim()) onSubmit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      submit();
    }
  };

  const handleChange = (event: ChangeEvent<HTMLInputElement>) => {
    onChange(event.target.value);
  };

  return (
    <div id="poda" className={wide ? 'poda-wide' : undefined}>
      <div className="glow" />
      <div className="darkBorderBg" />
      <div className="darkBorderBg" />
      <div className="darkBorderBg" />
      <div className="white" />
      <div className="border" />
      <div id="main">
        <input
          className="input"
          name="text"
          type="text"
          placeholder={placeholder ?? 'Ask anything about your documents...'}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          disabled={disabled}
        />
        <div id="pink-mask" />
        <div className="filterBorder" />
        <button id="filter-icon" type="button" onClick={submit} disabled={disabled} aria-label="Send message">
          <svg fill="none" viewBox="0 0 24 24" width="20" height="20">
            <path
              stroke="#d6d6e6"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M22 2L11 13M22 2L15 22L11 13L2 9L22 2Z"
            />
          </svg>
        </button>
        <div id="search-icon">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="17"
            height="17"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </div>
      </div>
    </div>
  );
}
