import { Redirect } from 'expo-router';

export default function Index() {
  // Direct entry point: redirect to splash screen
  return <Redirect href="/(auth)/splash" />;
}
