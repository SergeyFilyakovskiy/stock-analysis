import { Switch, Route, Router } from "wouter";
import { useHashLocation } from "wouter/use-hash-location";
import { Toaster } from "@/components/ui/toaster";
import { useAuth } from "./lib/auth-context";

import LoginPage from "./pages/login";
import RegisterPage from "./pages/register";
import OAuthCallbackPage from "./pages/oauth-callback";
import DashboardLayout from "./layouts/dashboard-layout";
import MarketPage from "./pages/market";
import ChartPage from "./pages/chart";
import FundamentalsPage from "./pages/fundamentals";
import ScreenerPage from "./pages/screener";
import ComparePage from "./pages/compare";
import NotFound from "./pages/not-found";

export default function App() {
  const { isAuthenticated } = useAuth();

  return (
    <Router hook={useHashLocation}>
      <Switch>
        {/* Public routes */}
        <Route path="/login" component={LoginPage} />
        <Route path="/register" component={RegisterPage} />
        <Route path="/oauth/callback" component={OAuthCallbackPage} />

        {/* Protected routes */}
        {isAuthenticated ? (
          <Route>
            <DashboardLayout>
              <Switch>
                <Route path="/" component={MarketPage} />
                <Route path="/chart/:ticker" component={ChartPage} />
                <Route path="/fundamentals/:ticker" component={FundamentalsPage} />
                <Route path="/screener" component={ScreenerPage} />
                <Route path="/compare" component={ComparePage} />
                <Route component={NotFound} />
              </Switch>
            </DashboardLayout>
          </Route>
        ) : (
          <Route>
            <LoginPage />
          </Route>
        )}
      </Switch>
      <Toaster />
    </Router>
  );
}
