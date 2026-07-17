import { Theme } from './settings/types';
import { NightShiftLanding } from './components/generated/NightShiftLanding';

let theme: Theme = 'dark';

function App() {
  function setTheme(theme: Theme) {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  setTheme(theme);

  return (
    <>
      <NightShiftLanding />
    </>
  ); // %EXPORT_STATEMENT%
}

export default App;
