import {
  Children,
  isValidElement,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type KeyboardEvent,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import { Check, ChevronDown } from 'lucide-react';

const MENU_GAP = 6;
const VIEWPORT_PADDING = 8;
const MENU_MAX_HEIGHT = 280;
const MENU_MIN_WIDTH = 180;
const OPTION_HEIGHT = 44;
const TYPEAHEAD_TIMEOUT_MS = 700;
type Option = { value: string; label: string; disabled: boolean };

export function Select({
  label,
  value,
  on_change,
  children,
  required = false,
  disabled = false,
}: {
  label: string;
  value: string | number;
  on_change: (value: string) => void;
  children: ReactNode;
  required?: boolean;
  disabled?: boolean;
}) {
  const menu_id = useId();
  const trigger_ref = useRef<HTMLButtonElement>(null);
  const menu_ref = useRef<HTMLDivElement>(null);
  const search_ref = useRef({ text: '', time: 0 });
  const [open, set_open] = useState(false);
  const [active_index, set_active_index] = useState(0);
  const [invalid, set_invalid] = useState(false);
  const [position, set_position] = useState({
    top: 0,
    left: 0,
    width: 0,
    maxHeight: MENU_MAX_HEIGHT,
  });
  const options: Option[] = Children.toArray(children).flatMap((child) => {
    if (!isValidElement<{ value: string | number; children: ReactNode; disabled?: boolean }>(child))
      return [];
    return [
      {
        value: String(child.props.value),
        label: Children.toArray(child.props.children).join(''),
        disabled: !!child.props.disabled,
      },
    ];
  });
  const selected_index = options.findIndex((option) => option.value === String(value));
  const is_open = open && !disabled;

  function show(index = selected_index) {
    const next_index =
      index >= 0 && !options[index]?.disabled
        ? index
        : options.findIndex((option) => !option.disabled);
    set_active_index(next_index);
    set_open(true);
  }
  function choose(index: number) {
    const option = options[index];
    if (!option || option.disabled) return;
    on_change(option.value);
    set_invalid(false);
    set_open(false);
  }
  function on_key_down(event: KeyboardEvent<HTMLButtonElement>) {
    if (event.key === 'Escape') {
      set_open(false);
      event.preventDefault();
    } else if (event.key === 'Tab') {
      set_open(false);
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      if (is_open) choose(active_index);
      else show();
    } else if (['ArrowDown', 'ArrowUp', 'Home', 'End'].includes(event.key)) {
      event.preventDefault();
      const enabled = options.flatMap((option, index) => (option.disabled ? [] : [index]));
      const current = enabled.indexOf(is_open ? active_index : selected_index);
      const next =
        event.key === 'Home'
          ? 0
          : event.key === 'End'
            ? enabled.length - 1
            : Math.max(
                0,
                Math.min(enabled.length - 1, current + (event.key === 'ArrowDown' ? 1 : -1)),
              );
      show(enabled[next]);
    } else if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      const now = Date.now();
      const text =
        (now - search_ref.current.time < TYPEAHEAD_TIMEOUT_MS ? search_ref.current.text : '') +
        event.key.toLocaleLowerCase();
      search_ref.current = { text, time: now };
      const index = options.findIndex(
        (option) => !option.disabled && option.label.toLocaleLowerCase().startsWith(text),
      );
      if (index >= 0) show(index);
      event.preventDefault();
    }
  }

  useLayoutEffect(() => {
    if (!is_open) return;
    function position_menu() {
      const rect = trigger_ref.current!.getBoundingClientRect();
      const below = window.innerHeight - rect.bottom - MENU_GAP - VIEWPORT_PADDING;
      const above = rect.top - MENU_GAP - VIEWPORT_PADDING;
      const desired = Math.min(MENU_MAX_HEIGHT, options.length * OPTION_HEIGHT);
      const upwards = below < desired && above > below;
      const height = Math.max(0, Math.min(desired, upwards ? above : below));
      const width = Math.min(
        Math.max(rect.width, MENU_MIN_WIDTH),
        window.innerWidth - VIEWPORT_PADDING * 2,
      );
      set_position({
        top: upwards ? rect.top - MENU_GAP - height : rect.bottom + MENU_GAP,
        left: Math.max(
          VIEWPORT_PADDING,
          Math.min(rect.left, window.innerWidth - width - VIEWPORT_PADDING),
        ),
        width,
        maxHeight: height,
      });
    }
    position_menu();
    window.addEventListener('resize', position_menu);
    window.addEventListener('scroll', position_menu, true);
    return () => {
      window.removeEventListener('resize', position_menu);
      window.removeEventListener('scroll', position_menu, true);
    };
  }, [is_open, options.length]);
  useEffect(() => {
    if (!is_open) return;
    function close_outside(event: PointerEvent) {
      const target = event.target as Node;
      if (!trigger_ref.current?.contains(target) && !menu_ref.current?.contains(target))
        set_open(false);
    }
    document.addEventListener('pointerdown', close_outside);
    return () => document.removeEventListener('pointerdown', close_outside);
  }, [is_open]);
  useEffect(() => {
    if (is_open)
      document.getElementById(`${menu_id}-${active_index}`)?.scrollIntoView({ block: 'nearest' });
  }, [is_open, active_index, menu_id]);

  return (
    <span className="select-field">
      <button
        ref={trigger_ref}
        type="button"
        role="combobox"
        className="select-trigger"
        aria-label={label}
        aria-expanded={is_open}
        aria-haspopup="listbox"
        aria-controls={is_open ? menu_id : undefined}
        aria-activedescendant={
          is_open && active_index >= 0 ? `${menu_id}-${active_index}` : undefined
        }
        aria-required={required}
        aria-invalid={invalid || undefined}
        aria-describedby={invalid ? `${menu_id}-error` : undefined}
        disabled={disabled}
        onClick={() => (is_open ? set_open(false) : show())}
        onKeyDown={on_key_down}
        onBlur={() => set_open(false)}
      >
        <span>{options[selected_index]?.label || 'Выберите'}</span>
        <ChevronDown size={16} aria-hidden="true" />
      </button>
      {/* Скрытый select сохраняет нативную проверку обязательного поля формы. */}
      <select
        hidden
        aria-hidden="true"
        tabIndex={-1}
        value={value}
        required={required}
        disabled={disabled}
        onChange={(event) => on_change(event.target.value)}
        onInvalid={(event) => {
          event.preventDefault();
          set_invalid(true);
          trigger_ref.current?.focus();
        }}
      >
        {children}
      </select>
      {invalid && (
        <small id={`${menu_id}-error`} className="field-error">
          Выберите значение.
        </small>
      )}
      {is_open &&
        createPortal(
          <div
            ref={menu_ref}
            id={menu_id}
            role="listbox"
            aria-label={label}
            className="select-menu"
            style={position}
            onMouseDown={(event) => event.preventDefault()}
          >
            {options.map((option, index) => (
              <div
                key={option.value}
                id={`${menu_id}-${index}`}
                role="option"
                aria-selected={index === selected_index}
                aria-disabled={option.disabled || undefined}
                className={index === active_index ? 'select-option active' : 'select-option'}
                onPointerMove={() => !option.disabled && set_active_index(index)}
                onClick={() => choose(index)}
              >
                <span>{option.label}</span>
                {index === selected_index && <Check size={16} aria-hidden="true" />}
              </div>
            ))}
          </div>,
          document.body,
        )}
    </span>
  );
}
