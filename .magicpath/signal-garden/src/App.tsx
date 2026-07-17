import { Theme } from './settings/types';
import { SignalGardenLanding } from './components/generated/SignalGardenLanding';

let theme: Theme = 'light';

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
      <SignalGardenLanding />
    </>
  ); // %EXPORT_STATEMENT%
}

export default App;
