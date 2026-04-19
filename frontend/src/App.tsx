import { RouterProvider } from 'react-router-dom'
import { router } from './config/routes'
import { AssetsProvider } from './stores/AssetsContext'

export default function App() {
  return (
    <AssetsProvider>
      <RouterProvider router={router} />
    </AssetsProvider>
  )
}
