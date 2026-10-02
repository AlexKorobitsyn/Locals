import { expect, it } from 'vitest';
import { can_create_scene, can_edit_public, can_moderate } from './permissions';

it('allows proposals at zero XP and keeps foreign editing exclusive to moderators', () => {
  for (const level of ['green', 'experienced']) {
    expect(can_create_scene(level)).toBe(true);
    expect(can_edit_public(false, level)).toBe(false);
    expect(can_edit_public(true, level)).toBe(true);
    expect(can_moderate(level)).toBe(false);
  }
  for (const level of ['moderator', 'admin']) {
    expect(can_edit_public(false, level)).toBe(true);
    expect(can_moderate(level)).toBe(true);
  }
  expect(can_create_scene()).toBe(false);
});
