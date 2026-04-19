import { RouterProvider } from 'react-router-dom'
import { router } from './config/routes'
import { AssetsProvider } from './stores/AssetsProvider'
import { CashAccountsProvider } from './stores/CashAccountsProvider'
import { IncomeProvider } from './stores/IncomeProvider'
import { UserSettingsProvider } from './stores/UserSettingsProvider'
import { WealthFreedomProvider } from './stores/WealthFreedomProvider'

export default function App() {
  return (
    <AssetsProvider>
      <UserSettingsProvider>
        <CashAccountsProvider>
          <IncomeProvider>
            <WealthFreedomProvider>
              <RouterProvider router={router} />
            </WealthFreedomProvider>
          </IncomeProvider>
        </CashAccountsProvider>
      </UserSettingsProvider>
    </AssetsProvider>
  )
}
