import React, { createContext, useContext, useState } from 'react';

const LearningContext = createContext({});

export function LearningProvider({ children }) {
  const [state, setState] = useState({});
  return (
    <LearningContext.Provider value={{ state, setState }}>
      {children}
    </LearningContext.Provider>
  );
}

export function useLearning() {
  return useContext(LearningContext);
}

export default LearningContext;