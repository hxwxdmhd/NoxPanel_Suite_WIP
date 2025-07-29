import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { api, Script, ExecutionResult } from '../../services/api';
import toast from 'react-hot-toast';

const Container = styled(motion.div)`
  padding: 1.5rem;
  background: var(--surface-color);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 2rem;
`;

const Header = styled.div`
  display: flex;
  justify-content: between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
`;

const Title = styled.h2`
  color: var(--text-color);
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const FilterBar = styled.div`
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
`;

const SearchInput = styled.input`
  padding: 0.5rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  background: var(--background-color);
  color: var(--text-color);
  font-size: 0.9rem;
  min-width: 200px;

  &:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 2px rgba(var(--primary-color), 0.2);
  }
`;

const TagFilter = styled.select`
  padding: 0.5rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  background: var(--background-color);
  color: var(--text-color);
  font-size: 0.9rem;
`;

const ScriptGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
`;

const ScriptCard = styled(motion.div)<{ isExecuting?: boolean }>`
  background: var(--background-color);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  transition: all var(--transition-duration) ease;
  cursor: pointer;
  opacity: ${props => props.isExecuting ? 0.7 : 1};

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
    border-color: var(--primary-color);
  }
`;

const ScriptName = styled.h3`
  color: var(--text-color);
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0 0 0.5rem 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const ScriptDescription = styled.p`
  color: rgba(var(--text-color), 0.8);
  font-size: 0.9rem;
  margin: 0 0 1rem 0;
  line-height: 1.4;
`;

const ScriptMeta = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.8rem;
  color: rgba(var(--text-color), 0.6);
  margin-bottom: 1rem;
`;

const ScriptTags = styled.div`
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
`;

const Tag = styled.span`
  background: var(--primary-color);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
`;

const ScriptActions = styled.div`
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-duration) ease;

  ${props => {
    switch (props.variant) {
      case 'primary':
        return `
          background: var(--primary-color);
          color: white;
          &:hover { opacity: 0.9; transform: translateY(-1px); }
        `;
      case 'secondary':
        return `
          background: var(--secondary-color);
          color: white;
          &:hover { opacity: 0.9; transform: translateY(-1px); }
        `;
      case 'danger':
        return `
          background: #dc3545;
          color: white;
          &:hover { opacity: 0.9; transform: translateY(-1px); }
        `;
      default:
        return `
          background: rgba(255, 255, 255, 0.1);
          color: var(--text-color);
          &:hover { background: rgba(255, 255, 255, 0.2); }
        `;
    }
  }}

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }
`;

const LoadingSpinner = styled(motion.div)`
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid var(--primary-color);
  border-radius: 50%;
  display: inline-block;
  margin-right: 0.5rem;
`;

const ExecutionModal = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
`;

const ModalContent = styled(motion.div)`
  background: var(--surface-color);
  border-radius: 12px;
  padding: 2rem;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
`;

const OutputContainer = styled.pre`
  background: var(--background-color);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1rem;
  color: var(--text-color);
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
  white-space: pre-wrap;
  max-height: 300px;
  overflow-y: auto;
  margin: 1rem 0;
`;

const ScriptManager: React.FC = () => {
  const { currentTheme } = useTheme();
  const queryClient = useQueryClient();

  const [searchTerm, setSearchTerm] = useState('');
  const [tagFilter, setTagFilter] = useState('all');
  const [executingScript, setExecutingScript] = useState<string | null>(null);
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [showExecutionModal, setShowExecutionModal] = useState(false);

  // Fetch scripts
  const { data: scriptsData, isLoading, error } = useQuery(
    'scripts',
    api.getScripts,
    {
      refetchInterval: 30000, // Refresh every 30 seconds
    }
  );

  // Execute script mutation
  const executeScriptMutation = useMutation(
    ({ scriptPath, args }: { scriptPath: string; args: string[] }) =>
      api.executeScript(scriptPath, args),
    {
      onMutate: ({ scriptPath }) => {
        setExecutingScript(scriptPath);
      },
      onSuccess: (response, { scriptPath }) => {
        const result = response.data as ExecutionResult;
        setExecutionResult(result);
        setShowExecutionModal(true);

        if (result.success) {
          toast.success(`Script ${scriptPath} executed successfully`);
        } else {
          toast.error(`Script ${scriptPath} failed`);
        }

        // Refresh execution history
        queryClient.invalidateQueries('executionHistory');
      },
      onError: (error, { scriptPath }) => {
        toast.error(`Failed to execute ${scriptPath}`);
        console.error('Script execution error:', error);
      },
      onSettled: () => {
        setExecutingScript(null);
      },
    }
  );

  const scripts = scriptsData?.data?.scripts || [];

  // Filter scripts
  const filteredScripts = scripts.filter((script: Script) => {
    const matchesSearch = script.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         script.description.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesTag = tagFilter === 'all' || script.tags.includes(tagFilter);

    return matchesSearch && matchesTag;
  });

  // Get all unique tags
  const allTags = Array.from(
    new Set(scripts.flatMap((script: Script) => script.tags))
  ).sort();

  const getScriptIcon = (type: string) => {
    const icons = {
      py: '🐍',
      ps1: '💻',
      sh: '🐚',
      bat: '⚡',
      js: '📜',
    };
    return icons[type] || '📄';
  };

  const handleExecuteScript = (scriptPath: string) => {
    executeScriptMutation.mutate({ scriptPath, args: [] });
  };

  const closeExecutionModal = () => {
    setShowExecutionModal(false);
    setExecutionResult(null);
  };

  if (isLoading) {
    return (
      <Container>
        <div style={{ textAlign: 'center', padding: '2rem' }}>
          <LoadingSpinner
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
          />
          Loading scripts...
        </div>
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <div style={{ textAlign: 'center', padding: '2rem', color: '#dc3545' }}>
          ❌ Failed to load scripts. Please check your connection.
        </div>
      </Container>
    );
  }

  return (
    <>
      <Container
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Header>
          <Title>
            🚀 Script Manager
            <span style={{ fontSize: '0.9rem', opacity: 0.7 }}>
              ({filteredScripts.length} scripts)
            </span>
          </Title>

          <FilterBar>
            <SearchInput
              type="text"
              placeholder="Search scripts..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />

            <TagFilter
              value={tagFilter}
              onChange={(e) => setTagFilter(e.target.value)}
            >
              <option value="all">All Tags</option>
              {allTags.map(tag => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
            </TagFilter>
          </FilterBar>
        </Header>

        <ScriptGrid>
          <AnimatePresence>
            {filteredScripts.map((script: Script) => (
              <ScriptCard
                key={script.path}
                isExecuting={executingScript === script.path}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }}
                transition={{ duration: 0.3 }}
              >
                <ScriptName>
                  {getScriptIcon(script.type)} {script.name}
                </ScriptName>

                <ScriptDescription>
                  {script.description}
                </ScriptDescription>

                <ScriptMeta>
                  <span>{script.type.toUpperCase()}</span>
                  <span>{(script.size / 1024).toFixed(1)} KB</span>
                  <span>{new Date(script.modified).toLocaleDateString()}</span>
                </ScriptMeta>

                {script.tags.length > 0 && (
                  <ScriptTags>
                    {script.tags.map(tag => (
                      <Tag key={tag}>{tag}</Tag>
                    ))}
                  </ScriptTags>
                )}

                <ScriptActions>
                  <Button
                    variant="primary"
                    onClick={() => handleExecuteScript(script.path)}
                    disabled={executingScript === script.path}
                  >
                    {executingScript === script.path ? (
                      <>
                        <LoadingSpinner
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                        />
                        Running...
                      </>
                    ) : (
                      '▶️ Execute'
                    )}
                  </Button>

                  <Button onClick={() => {
                    // TODO: Implement script editing
                    toast.info('Script editing coming soon!');
                  }}>
                    ✏️ Edit
                  </Button>
                </ScriptActions>
              </ScriptCard>
            ))}
          </AnimatePresence>
        </ScriptGrid>

        {filteredScripts.length === 0 && (
          <div style={{ textAlign: 'center', padding: '2rem', opacity: 0.7 }}>
            No scripts found matching your criteria.
          </div>
        )}
      </Container>

      {/* Execution Result Modal */}
      <AnimatePresence>
        {showExecutionModal && executionResult && (
          <ExecutionModal
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeExecutionModal}
          >
            <ModalContent
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <h3 style={{ color: 'var(--text-color)', marginTop: 0 }}>
                Execution Result
                {executionResult.success ? ' ✅' : ' ❌'}
              </h3>

              <div style={{ marginBottom: '1rem', fontSize: '0.9rem', opacity: 0.8 }}>
                <strong>Execution Time:</strong> {executionResult.execution_time.toFixed(2)}s
                <br />
                <strong>Timestamp:</strong> {new Date(executionResult.timestamp).toLocaleString()}
              </div>

              {executionResult.output && (
                <div>
                  <h4 style={{ color: 'var(--text-color)' }}>Output:</h4>
                  <OutputContainer>{executionResult.output}</OutputContainer>
                </div>
              )}

              {executionResult.error && (
                <div>
                  <h4 style={{ color: '#dc3545' }}>Error:</h4>
                  <OutputContainer style={{ borderColor: '#dc3545', color: '#dc3545' }}>
                    {executionResult.error}
                  </OutputContainer>
                </div>
              )}

              <div style={{ textAlign: 'right', marginTop: '1rem' }}>
                <Button variant="primary" onClick={closeExecutionModal}>
                  Close
                </Button>
              </div>
            </ModalContent>
          </ExecutionModal>
        )}
      </AnimatePresence>
    </>
  );
};

export default ScriptManager;
