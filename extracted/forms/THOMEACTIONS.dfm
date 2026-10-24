object HomeActions: THomeActions
  object List: TUiActionList
    object FindAction: TUiAction
      Category = 'Search'
      Hint = 'Find|Finds search string.'
      ShortCutStr = 'Ctrl+F'
    end
    object ShowManageAction: TUiAction
      Category = 'View'
      Caption = 'Show Session &Management'
      Hint = 'Show Session Management|Shows or hides management panel.'
    end
    object MaximizeManageAction: TUiAction
      Category = 'View'
      AutoCheck = True
      Caption = 'Ma&ximize Session Management'
      Hint = 'Maximize Session Management|Maximizes or restores management panel.'
    end
    object ShowWebAction: TUiAction
      Category = 'View'
      Caption = 'Show &Web Resources'
      Hint = 'Show Web Resources|Shows or hides web panel.'
    end
  end
  object Tree: TUiActionTree
    Nodes = ('MergeFile: Menu', (), 'View: Menu', ('ShowManage: MenuItem', 'MaximizeManage: MenuItem', 'ShowWeb: MenuItem'))
  end
end
