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
      </div>
    </div>
  );
}
