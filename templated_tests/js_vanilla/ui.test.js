// ui.test.js
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import UI from './ui';

describe('UI Class', () => {
  let ui;
  let document;
  let profileElement;

  beforeEach(() => {
    const dom = new JSDOM(`
      <div id="profile"></div>
      <div class="searchContainer">
        <div class="search"></div>
      </div>
    `);
    document = dom.window.document;
    global.document = document;
    global.window = dom.window;

    profileElement = document.getElementById('profile');
    ui = new UI();
  });

  it('should instantiate the UI class', () => {
    expect(ui).toBeDefined();
  });
});
