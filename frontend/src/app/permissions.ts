export function can_moderate(level?: string) {
  return level === 'moderator' || level === 'admin';
}

export function can_edit_public(is_owner: boolean | undefined, level?: string) {
  return !!is_owner || can_moderate(level);
}

export function can_create_scene(level?: string, _experience?: unknown) {
  return !!level;
}
